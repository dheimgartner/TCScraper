# tcsscraper

- Tools to scrape the TCS database (which is based on the BFE)
- https://www.verbrauchskatalog.ch/index.php
- The interesting aspect: it allows you to compute various (cost) measures based on the canton, mileague, car type (so it is dynamic).
- Therefore it is a suitable set of tools to found your cost assumptions on and trace out other vehicle related attributes (for an SP).

Read more about packaging here: https://packaging.python.org/en/latest/tutorials/packaging-projects/
=> contains hints to valuable further resources (such as "scaffolding frameworks")...

## Some remarks on packaging
- `pip install -e .` (run from your root) is very useful for testing (similar to R's `devtools::load_all()` but I think it automatically updates...).
    - (however this requires to use `setuptools` and `setup.py` (does not work with hatchling))
        - => **WRONG** just needed to update pip ;) => `pip install --upgrade pip`
    - see https://packaging.python.org/guides/distributing-packages-using-setuptools/
- Write tests with `unittest`
    - Run with `python -m unittest test_module.test_class` (or similar from your tests directory)
    - => run pip install -e first to avoid NoModuleNamed blabla confusion!