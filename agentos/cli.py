"""AgentOS command line interface (CLI).

The CLI allows creation of a simple template agent.
"""
import agentos
import click
from datetime import datetime
import gym
import mlflow.projects
import importlib.util
from pathlib import Path
import configparser
import importlib
import sys

CONDA_ENV_FILE = Path("./conda_env.yaml")
CONDA_ENV_CONTENT = """{file_header}

name: {agent_name}

dependencies:
    - pip
    - pip:
      - gym
      - agentos
      # Or, if you want to use your local copy of agentos, then
      # update the line below and replace the line above with it.
      #- -e path/to/agentos/git/repo
"""

MLFLOW_PROJECT_FILE = Path("./MLProject")
MLFLOW_PROJECT_CONTENT = """{file_header}

name: {agent_name}

conda_env: {conda_env}

entry_points:
  main:
    command: "python main.py"
"""

AGENT_DEF_FILE = Path("./agent.py")  # Default location of agent code.
AGENT_MAIN_FILE = Path("./main.py")
AGENT_CODE = """{file_header}
import agentos


# A basic agent.
class {agent_name}(agentos.Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.obs = self.environment.reset()

    def train(self):
        self.trainer.train(self.policy)

    def advance(self):
        next_action = self.policy.decide(
            self.obs,
            self.environment.valid_actions
        )
        self.obs, reward, done, info = self.environment.step(next_action)
        return done
"""


ENV_DEF_FILE = Path("./environment.py")
ENV_CODE = """{file_header}
import agentos


# Simulates a 1D corridor
class Corridor(agentos.Environment):
    def __init__(self):
        self.length = 5
        self.action_space = [0, 1]
        self.observation_space = [0, 1, 2, 3, 4, 5]
        self.reset()

    def step(self, action):
        assert action in self.action_space
        if action == 0:
            self.position = max(self.position - 1, 0)
        else:
            self.position = min(self.position + 1, self.length)
        return (self.position, -1, self.done, {{}})

    def reset(self):
        self.position = 0
        return self.position

    @property
    def valid_actions(self):
        return self.action_space

    @property
    def done(self):
        return self.position >= self.length
"""

POLICY_DEF_FILE = Path("./policy.py")
POLICY_CODE = """{file_header}
import agentos
import random


# A random policy
class RandomPolicy(agentos.Policy):
    def decide(self, observation, actions):
        return random.choice(actions)
"""

TRAINER_DEF_FILE = Path("./trainer.py")
TRAINER_CODE = """{file_header}
import agentos


# A no-op trainer
class NoOpTrainer(agentos.Trainer):
    def train(self, policy):
        return policy
"""

AGENT_INI_FILE = Path("./agent.ini")
AGENT_INI_CONTENT = """
[Agent]
class = agent.{agent_name}

[Environment]
class = environment.Corridor

[Policy]
class = policy.RandomPolicy

[Trainer]
class = trainer.NoOpTrainer
"""

INIT_FILES = {
    CONDA_ENV_FILE: CONDA_ENV_CONTENT,
    MLFLOW_PROJECT_FILE: MLFLOW_PROJECT_CONTENT,
    AGENT_DEF_FILE: AGENT_CODE,
    ENV_DEF_FILE: ENV_CODE,
    POLICY_DEF_FILE: POLICY_CODE,
    TRAINER_DEF_FILE: TRAINER_CODE,
    AGENT_INI_FILE: AGENT_INI_CONTENT,
}


@click.group()
@click.version_option()
def agentos_cmd():
    pass


def validate_agent_name(ctx, param, value):
    if " " in value or ":" in value or "/" in value:
        raise click.BadParameter("name may not contain ' ', ':', or '/'.")
    return value


@agentos_cmd.command()
@click.argument("dir_names", nargs=-1, metavar="DIR_NAMES")
@click.option(
    "--agent-name",
    "-n",
    metavar="AGENT_NAME",
    default="BasicAgent",
    callback=validate_agent_name,
    help="This is used as the name of the MLflow Project and "
    "Conda env for all *Directory Agents* being created. "
    "AGENT_NAME may not contain ' ', ':', or '/'.",
)
def init(dir_names, agent_name):
    """Initialize current (or specified) directory as an AgentOS agent.

    \b
    Arguments:
        [OPTIONAL] DIR_NAMES zero or more space separated directories to
                             initialize. They will be created if they do
                             not exist.

    Creates an agent main.py file, a conda env, and an MLflow project file
    in all directories specified, or if none are specified, then create
    the files in current directory.
    """
    dirs = [Path(".")]
    if dir_names:
        dirs = [Path(d) for d in dir_names]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        for file_path, content in INIT_FILES.items():
            f = open(d / file_path, "w")
            now = datetime.now().strftime("%b %d, %Y %H:%M:%S")
            header = (
                f"# This file was auto-generated by `agentos init` on {now}."
            )
            f.write(
                content.format(
                    agent_name=agent_name,
                    conda_env=CONDA_ENV_FILE.name,
                    file_header=header,
                )
            )
            f.flush()

        d = "current working directory" if d == Path(".") else d
        click.echo(
            f"Finished initializing AgentOS agent '{agent_name}' in {d}."
        )


def _get_subclass_from_file(filename, parent_class):
    """Return first subclass of `parent_class` found in filename, else None."""
    path = Path(filename)
    assert path.is_file(), f"Make {path} is a valid file."
    assert path.suffix == ".py", "Filename must end in .py"

    spec = importlib.util.spec_from_file_location(path.stem, path.absolute())
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for elt in module.__dict__.values():
        if type(elt) is type and issubclass(elt, parent_class):
            print(f"Found first subclass class {elt}; returning it.")
            return elt


def get_class_from_config(class_path):
    split_path = class_path.split(".")
    class_name = split_path[-1]
    module_name = ".".join(split_path[:-1])
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def load_agent_from_current_directory():
    sys.path.append(".")
    agent_file = Path("./agent.ini")
    config = configparser.ConfigParser()
    config.read(agent_file)
    agent_cls = get_class_from_config(config["Agent"]["class"])
    policy_cls = get_class_from_config(config["Policy"]["class"])
    environment_cls = get_class_from_config(config["Environment"]["class"])
    trainer_cls = get_class_from_config(config["Trainer"]["class"])
    # TODO - intialize classes with configs
    return agent_cls(environment_cls(), policy_cls(), trainer_cls())


@agentos_cmd.command()
@click.argument("iters", type=click.INT, required=True)
def train(iters):
    agent = load_agent_from_current_directory()
    for i in range(iters):
        agent.train()


@agentos_cmd.command()
def test():
    agent = load_agent_from_current_directory()
    done = False
    step_count = 0
    while not done:
        done = agent.advance()
        step_count += 1
    print(f"Agent finished in {step_count} steps")


@agentos_cmd.command()
@click.argument("run_args", nargs=-1, metavar="RUN_ARGS")
@click.option(
    "--hz",
    "-h",
    metavar="HZ",
    default=40,
    type=int,
    help="Frequency to call agent.advance().",
)
@click.option(
    "--max-iters",
    "-m",
    metavar="MAX_STEPS",
    type=int,
    default=None,
    help="Stop running agent after this many calls to advance().",
)
def run(run_args, hz, max_iters):
    """Run an AgentOS agent (agentos.Agent) with an environment (gym.Env).

    \b
    Arguments:
        RUN_ARGS: 0, 1, or 2 space delimited arguments, parsed as follows:

    \b
    If no args are specified, look for default files defining agent:
        - look for file named `MLProject` or `main.py` in the current working
          directory and if found, run this directory as an MLflow project.
              - Try to use MLProject file first, using whatever it defines
                as main entry point, and if that doesn't exist
                then run using MLflow without MLProject passing main.py
                as the entry point (note that this will ignore a conda
                environment file if one exists and MLflow will create
                a new essentially empty conda env).
        - else, look for file named `agent.py` in current working
          directory and, if found, then behave in the same was as if 1
          argument (i.e., `agent.py`) was provided, as described below.
    Else, if 1 arg is specified, interpret it as `agent_filename`:
        - if it is a directory name, assume it is an AgentOS agent dir,
          and behavior is equivalent of navigating into that directory
          and running `agentos run` (without arguments) in it (see above).
        - if it is a file name, the file must contain an agent class and env
          class definition. AgentOS searches that file for the first subclass
          of agentos.Agent, as well as first subclass of gym.Env and calls
          agentos.run_agent() passing in the agent and env classes found.
    Else, if 2 args specified, interpret as either filenames or py classes.
         - assume the first arg specifies the agent and second specifies
           the Env. The following parsing rules are applied independently
           to each of the two args (e.g., filenames and classes can be mixed):
             - if the arg is a filename:
                  Look for the first instance of the appropriate subclass
                  (either agentos.Agent or gym.env) in the file and use that
                  as the argument to agentos.run_agent.
              - else:
                  Assume the arg is in the form [package.][module.]classname
                  and that it is available in this python environments path.

    """

    def _handle_no_run_args(dirname=None):
        if dirname:
            agent_dir = Path(dirname)
            assert agent_dir.is_dir()
        else:
            agent_dir = Path("./")
        if (agent_dir / MLFLOW_PROJECT_FILE).is_file():
            print("Running agent in this dir via MLflow.")
            mlflow.projects.run(str(agent_dir.absolute()))
            return
        elif (agent_dir / AGENT_MAIN_FILE).is_file():
            print(
                f"Running agent in this dir via MLflow with "
                f"entry point {AGENT_MAIN_FILE}."
            )
            mlflow.projects.run(
                str(agent_dir.absolute()), entry_point=AGENT_MAIN_FILE.name
            )
        else:
            if not (agent_dir / AGENT_DEF_FILE).is_file():
                raise click.UsageError(
                    "No args were passed to run, so one "
                    f"of {MLFLOW_PROJECT_FILE}, "
                    f"{AGENT_MAIN_FILE}, "
                    f"{AGENT_DEF_FILE} must exist."
                )
            _handle_single_run_arg(agent_dir / AGENT_DEF_FILE)

    def _handle_single_run_arg(filename):
        """The file must contain:
        - 1 or more agentos.Agent subclass
        - 1 or more gym.Env subclass.
        """
        agent_cls = _get_subclass_from_file(filename, agentos.Agent)
        env_cls = _get_subclass_from_file(filename, gym.Env)
        assert agent_cls and env_cls, (
            f" {filename} must contain >= 1 agentos.Agent subclass "
            f"and >= 1 gym.Env subclass."
        )
        agentos.run_agent(agent_cls, env_cls, hz=hz, max_iters=max_iters)

    if len(run_args) == 0:
        _handle_no_run_args()
    elif len(run_args) == 1:
        if Path(run_args[0]).is_dir():
            _handle_no_run_args(run_args[0])
        if Path(run_args[0]).is_file():
            _handle_single_run_arg(run_args[0])
        else:
            raise click.UsageError(
                "1 argument was passed to run; it must be "
                "a filename and it is not. (The file "
                "should define your agent class.)"
            )
    elif len(run_args) == 2:
        agent_arg, env_arg = run_args[0], run_args[1]
        if Path(agent_arg).is_file():
            agent_cls = _get_subclass_from_file(agent_arg, agentos.Agent)
            assert (
                agent_cls
            ), f"{agent_arg} must contain a subclass of agentos.Agent"
        else:
            ag_mod_name = ".".join(agent_arg.split(".")[:-1])
            ag_cls_name = agent_arg.split(".")[-1]
            ag_mod = importlib.import_module(ag_mod_name)
            agent_cls = getattr(ag_mod, ag_cls_name)
        if Path(env_arg).is_file():
            env_cls = _get_subclass_from_file(env_arg, gym.Env)
            assert env_cls, f"{env_arg} must contain a subclass of gym.Env"
        else:
            env_mod_name = ".".join(env_arg.split(".")[:-1])
            env_cls_name = env_arg.split(".")[-1]
            env_mod = importlib.import_module(env_mod_name)
            env_cls = getattr(env_mod, env_cls_name)
        agentos.run_agent(agent_cls, env_cls, hz=hz, max_iters=max_iters)
    else:
        raise click.UsageError("run command can take 0, 1, or 2 arguments.")


if __name__ == "__main__":
    agentos_cmd()
