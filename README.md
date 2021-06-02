multipark_tweets
==============================

Comparing in and out of park tweets across cities for health/sentiment outcomes.

Includes code to pull tweets from UVM Storylab Mongodb database AKA hydra, process these tweets by finding ones inside of parks, assinging 'control' tweets, and then performing boostrapped sentiment analysis.

Also includes notebooks to produce plots, summary tables, and visualizations of relevant results.

Data is excluded from repository.

Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── notebooks          <- Jupyter notebooks 
    │   ├── figures        <- Figures generated from plot notebooks
    │   ├── plot           <- Notebooks to generate specific plots
    │   ├── present        <- Figures in format for presenting.
    │   ├── process        <- Notebooks to prototype tweet processing code    
    │   ├── results        <- Results generated from other notebook analyses
    │   ├── sentiment      <- Notebooks to run sentiment analyses on different subsets. 
    │   └── test           <- Notebooks to test scripts.    
    │  
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── func           <- Helper functions
    │   │
    │   ├── hydra          <- Scripts to pull raw data from Hydra, our tweet mongodb
    │   │
    │   ├── scripts        <- Utility scripts to process tweets on the cluster to train models and then use trained models to make
    │   │
    │   └── sentiment      <- Scripts to perform sentiment analysis
    │    
    │
    └── test_environment.py            <- File to check environment properly setuip.


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
