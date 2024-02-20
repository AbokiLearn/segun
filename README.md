# Aboki Segun

This is the source code for the `@AbokiSegun_bot` telegram bot.

## Local Development

Use the commands below to run this code locally:

```shell
# clone repository
git clone git@github.com:AbokiLearn/aboki-segun
cd aboki-segun

# install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Seeding the database

To populate the database with some example documents for testing purposes:

```shell
# download lecture content
./scripts/get_demo_lectures.sh

# populate database with documents
./scripts/seed_db.py
```
