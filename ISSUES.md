* AgentOS requirements conflicting with component reqs (e.g. differing numpy versions)


Goals from R2D22AOS presentation: 

https://docs.google.com/presentation/d/1PTpau4MnPsuTHqvLvFzoVnjfp1rlxETwSehd1w_IFGk/edit#slide=id.ge1071245f3_0_57

// * Store enough spec info in the registry to support R2D2
// * Machinery to reconstitute a spec and feed it to agent/policy
* Implement save/restore for replay buffer and the backing nets to allow `agentos {learn,run}` to function
// * Port the the core functionality of the Acme R2D2 agent to a separate repo and register it with ACR
* R2D2 from RLlib
* DEMO COMPLETE
* Tools to manage backing data (replay buffer, policy parameters, run stats)


See TODOs in r2d2 policy.py for more nitty gritty

## Shortcomings

* Environments using dm_env.  How will this play with Ray?  Adding dependencies
  like this for all environments is not ideal.

* I should port other environments to generate specs, should the default
  example one in AOS depend on dm_env?

* Pull out the template {agent, policy, env} files used by agentos init into
  their own files

* Policy.decide(obs, actions) needs the actions because it doesn't have a
  pointer to the environment and thus doesn't know the action_space

* Need to make environment automatically reset as in the gym env wrapper in
  Acme?

* Where should discount go (Acme wants it on the env, seems more like a policy
  thing to me)


## Next step

// * Env data in AOS registry
// * Start putting together pres of lessons learned (e.g. AOS requirements are tricky)

* Get persistence working
    * Policy.observe is implemented, implement in default agent loop
    * Test/train working in default agent
    * Actually dump network in r2d2
    * Maybe make a script to generate a fresh demo agent?

* port other environments to use spec, policy API (need to atleast get default agent working)
* look at R2D2 in RLlib


