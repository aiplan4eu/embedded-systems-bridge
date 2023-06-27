# Embedded Systems Bridge

This library provides general funcitonalities for using the [Unified Planning](https://github.com/aiplan4eu/unified-planning) library in robotic applications:
- helper functions to map object representations in your application domain to the UP domain and vice versa, e.g., to retrieve executable actions from a generated UP plan
- plan dispatchers for automated execution of action plans
- plan monitoring for validating action execution and performing precondition checks on subsequent actions

## Application examples

To see the Embedded Systems Bridge in use, please refer to our related repositories:
- [drone experiment](https://github.com/franklinselva/genom3-experiment/)
- [pick-and-place robot environment](https://github.com/DFKI-NI/mobipick_labs)


## Pre-commit Hooks


This repo has [pre-commit](https://pre-commit.com/) configurations. You can use this locally and set it up to run automatically before you commit something. To install, use pip:

```bash
pip3 install --user pre-commit
```

To run over all the files in the repo manually:

```bash
pre-commit run --all-files
```

To run pre-commit automatically before committing in the local repo, install the git hooks:

```bash
pre-commit install
```


## Acknowledgments

<img src="https://www.aiplan4eu-project.eu/wp-content/uploads/2021/07/euflag.png" width="60" height="40">

This library is being developed for the AIPlan4EU H2020 project (https://aiplan4eu-project.eu) that is funded by the European Commission under grant agreement number 101016442.
