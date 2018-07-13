# CaseDiscrete
Repository for Case Studies in Discrete Optimization. 

This repo wishes to minimize the total distance walked in a warehouse. Full mathematical description of the model is found in `Technical Documentation.pdf`.

## Requirements
This project uses Python 3.6.4. 
This project requires `gurobipy` among other packages. `gurobipy` is used with an academic licence.

This project requires that the user makes a folder `data` on the top level. 
This folder should entail a distance csv for the shortest distances in the warehouse. 
This forlder should also entail a csv file specify all the order details.
None of these files are pushed to Github as this is private Company information.

### Run Program
In order to run the program the above requirements must be satisfied. Then type the following commands in Terminal/Command Line
```
cd src
python3 main.py
```

## Code Style Agreement
### Git Use
- `master` branch is used as base and should always have running code. An extra `dev` branch will be considered ones the project exceeds 1000 code lines. Feature branches are used for new code. Every pull request into `master` should be approved by another user, and the Trello card for that task should in the pull request message.
- Commit messages should be well written and written in imperative, to keep the history good.

### Python Code Style

All code should try to follow the PEP8 style guide, most importantly:
- snake_casing for everything that is not a Class, which use UpperCamelCasing
- 4 spaces for tab
https://www.python.org/dev/peps/pep-0008/

All code and code commenting should try follow Google Docstring. This is a espectially important for major classes and functions.
https://google.github.io/styleguide/pyguide.html
http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
