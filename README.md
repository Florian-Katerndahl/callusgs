# callusgs

Implementation of USGS's machine-to-machine API 

## Features

`callusgs` is both a python package and a suite of command line tools.

## Installation

### Prerequisites

To fully use the package's/the API's functionality you need (1) an account at USGS and (2) access to M2M MACHINE role.
While the first one is mandatory, the functionality without access to the M2M MACHINE role is restricted.
The account credentials need to be passed to the command line tools via CLI arguments or by setting the environment variables
`USGS_USERNAME` and `USGS_AUTH`.

|              **Feature/Functionality**             | **Usable** |                               **Note**                               |
|:--------------------------------------------------:|:----------:|:--------------------------------------------------------------------:|
| Searching for scenes                               | Yes        |                                                                      |
| Creating scene lists out of search results         | Yes        |                                                                      |
| Generate orders from scene searches or scene lists | No         | Downloading orders from list, when order was placed via webinterface |
| Geocoding                                          | Yes        |                                                                      |
| WRS1/WRS2 to coordinate transformation             | Yes        |                                                                      |

Install the package together with the respective command line applications from pip.

```bash
pip install callusgs
```

Alternatively, if you're only interested in the CLI functionality of this tool the best choice is probably to use [pipx](https://github.com/pypa/pipx) for installation.

```bash
pipx install callusgs
```

## Usage

For more detailed usage instructions and/or examples, please refer to the [documentation](https://callusgs.readthedocs.io) or see the section below.

### Command Line Tool Examples

#### Download

The snippet below queries the EarthExplorer catalogue for Landsat 8/9 Collection 2 Level 2 scenes between June 1st, 2020 and
July 25th, 2024 for a small part of the southwest of Berlin, Germany. Additionally, only scenes for August and September are 
returned and they must have a cloudcover of no more than 15%. Results are stored in a directory called `download`. The user 
set the logging level to `INFO` with the `-v` flag.

```bash
callusgs -v download --product landsat_etm_c2_l2 \
    --date 2020-06-01 2024-07-25 --month aug sep \
    --cloudcover 0 15 --aoi-coordinates 52.5 13.4 52.5 13.2 52.7 13.2 52.5 13.4 -- download
```

The snippet below queries the EarthExplorer catalogue for Landsat 7 Collection 2 Level 1 scenes between January 1st, 2005 and
January 1st, 2020 for Lima, Peru, and its surrounding region. For the given polygon, the minimum bound recatangle is build and used for the query.
No further restrictions regarding the obervation months or cloudcouver are posed. Results **would be** stored in a directory called `download`,
but as a dry run is requested, only the number of available scenes and their download size is reported. The user requested extended debug output with
the `-vv` flag.

```bash
callusgs -vv --dry-run download --product landsat_etm_c2_l1 \
    --date 2005-01-01 2020-01-01 --aoi-type Mbr \
    --aoi-coordinates -11.99 -77.13 -11.97 -77.00 -12.01 -76.88 -12.07 -76.88 -12.13 -76.89 -12.07 -77.16 -11.99 -77.13 -- \
    download
```

#### Geocode

```bash
callusgs geocode
```

#### Grid2ll

```bash
callusgs grid2ll
```

## Documentation

See the docs folder for raw documentation or visit [callusgs.readthedocs.io](https://callusgs.readthedocs.io).

## License

- `callusgs` is licensed under the [GPL-v2](LICENSE)
- the file `docs/requirements.txt` is licensed under the MIT license.

## Citation

If you use this software, please use the bibtex entry below or refer to [the citation file](CITATION.cff).

```
@software{callusgs,
author = {Katerndahl, Florian},
license = {GPL-2.0},
title = {{callusgs}},
url = {https://github.com/Florian-Katerndahl/callusgs}
}
```

## Acknowledgments

- Most of the docstrings were provided by the USGS in their API documentation.  
- The download application took initial inspiration from [the example script provided by the USGS](https://m2m.cr.usgs.gov/api/docs/example/download_data-py).
- `docs/requirements.txt` is taken from [here](https://docs.readthedocs.io/en/stable/guides/reproducible-builds.html)
