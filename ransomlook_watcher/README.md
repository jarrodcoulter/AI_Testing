# Ransomlook Watcher

This folder contains a small Python utility that monitors the public
[ransomlook.io](https://www.ransomlook.io/doc/) API for newly published
ransomware victims. The script keeps a lightweight JSON state file so that
subsequent executions only show entries that have not been seen before.

## Requirements

* Python 3.9+
* `requests`

You can install the dependency with:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python watch_ransomlook.py --limit 50
```

By default the script stores its state in
`~/.cache/ransomlook_watcher.json`. The location can be customised with the
`--state-file` argument or by setting the `RANSOMLOOK_STATE` environment
variable.

Useful command line options:

* `--limit`: number of victims retrieved from the API on each run (default: 25)
* `--show-all`: display all entries returned by the API rather than only new ones
* `--endpoint`: override the API path if the documented endpoint ever changes
* `--base-url`: allow watching self-hosted Ransomlook instances

If the script reports HTTP errors double check that your environment can reach
`https://www.ransomlook.io` and that your API key (if applicable) is valid.

## Running the tests

Automated tests exercise the most important pieces of the watcher without
contacting the live API. You can run them with:

```bash
python -m unittest discover -s tests -v
```
