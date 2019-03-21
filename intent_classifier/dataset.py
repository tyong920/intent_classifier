"""Components on datasets"""

import numpy as np

from .base import DataBunch


def load_from_mysql(configs: dict) -> DataBunch:
    """
    Load intent dataset from mysql database.

    Parameters
    ----------
    configs: Configs of mysql connnection, which includes keys:
        "host" - host of database,
        "port" - port of database
        "user" - user of database,
        "password" - password to login the database,
        "db" - database name of the dataset,
        "table" - table name of the dataset,
        "charset" - charset of the dataset, default value "utf8",
        "customer" - the customer's name.

    Returns
    -------
    Sklearn Bunch instance, including attributes:
    words - strings, user's words
    context - string in json format to offer extended features of context
    intent_labels - string, intent name in form of multi-levels
        separated with "," for multi-labels, such as
        "news/sports/football,person/story", which means labels
        "news/sports/football" and "person/story".

    """
    import pymysql

    for key in ["host", "port", "user", "password", "db", "table"]:
        assert key in configs, "mysql configs error!"

    words = []
    contexts = []
    intents = []

    db = pymysql.connect(host=configs["host"], port=configs["port"],
                         user=configs["user"], password=configs["password"])
    cursor = db.cursor()
    customer = configs.get("customer")
    if customer and customer != "common":
        sql = "select word, context, intent_labels " \
              "from {db}.{table} " \
              "where in_use=1 and customer in ('common', '{customer}')". \
            format(db=configs["db"], table=configs["table"],
                   customer=customer)
    else:
        sql = "select word, context, intent_labels " \
              "from {db}.{table} " \
              "where in_use=1 and customer='common'". \
            format(db=configs["db"], table=configs["table"])

    cursor.execute(sql)
    for word, context, intent_labels in cursor.fetchall():
        if not intent_labels:
            continue
        if not word and not context:
            continue
        words.append(word.lower()) if word else words.append("")
        contexts.append(context.lower()) if context else contexts.append("{}")
        intents.append(intent_labels.lower())

    cursor.close()
    db.close()

    return DataBunch(words=np.array(words, dtype=np.str),
                     contexts=np.array(contexts, dtype=np.str),
                     intents=np.array(intents, dtype=np.str))


def load_from_csv(csv_path: str) -> DataBunch:
    """
    Load intent dataset from csv file, which has fields:
    words - user's words.
            It could an empty string "" if no word input, like predict user's
            intent merely by context information.
    context - json format string.
            If no context information, it could as well be an empty string ""
            or "{}".
    intent_labels - labels of intent.
            String separated with ",", such as
            "news/sports/football,person/story", which means labels
            "news/sports/football" and "person/story".

    Parameters
    ----------
    csv_path: the path of the dataset file.

    Returns
    -------
    Sklearn Bunch instance, including attributes:
    words - strings, user's words
    context - string in json format to offer extended features of context
    intent_labels - string, intent name in form of multi-levels
        separated with "," for multi-labels, such as
        "news/sports/football,person/story", which means labels
        "news/sports/football" and "person/story".

    """
    import csv

    with open(csv_path) as f:
        csv_file = csv.reader(f)
        next(csv_file)      # skip the header
        words = []
        contexts = []
        intents = []
        for word, context, intent_labels in csv_file:
            if not word and (not context or context.strip()=="{}"):
                continue
            words.append(word)
            contexts.append(context) if context else context.append("{}")
            intents.append(intent_labels)

    return DataBunch(words=np.array(words, dtype=np.str),
                     contexts=np.array(contexts, dtype=np.str),
                     intents=np.array(intents, dtype=np.str))