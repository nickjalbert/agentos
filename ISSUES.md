* AgentOS requirements conflicting with component reqs (e.g. differing numpy versions)


Goals from R2D22AOS presentation: 

https://docs.google.com/presentation/d/1PTpau4MnPsuTHqvLvFzoVnjfp1rlxETwSehd1w_IFGk/edit#slide=id.ge1071245f3_0_57

//* Store enough spec info in the registry to support R2D2
//* Machinery to reconstitute a spec and feed it to agent/policy
* Implement save/restore for replay buffer and the backing nets to allow `agentos {learn,run}` to function
* Port the the core functionality of the Acme R2D2 agent to a separate repo and register it with ACR
* DEMO COMPLETE
* Tools to manage backing data (replay buffer, policy parameters, run stats)


See TODOs in r2d2 policy.py for more nitty gritty

## Shortcomings

* Environments using dm_env.  How will this play with Ray?  Adding dependencies
  like this for all environments is not ideal.


## Next step

* Env data in AOS registry
* Start putting together pres of lessons learned (e.g. AOS requirements are tricky)
