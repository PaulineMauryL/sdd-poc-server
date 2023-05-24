from datetime import datetime
import json
import yaml

from database.database import Database
from utils.constants import QUERIES_ARCHIVES


class YamlDatabase(Database):
    """
    Overall yaml in memory database management
    """

    def __init__(self, yaml_db_path) -> None:
        """
        Load DB
        """
        self.path = yaml_db_path
        with open(yaml_db_path, "r") as f:
            self.database = yaml.safe_load(f)
        self.queries_archives = []

    def does_user_exists(self, user_name: str) -> bool:
        """
        Checks if user exist in the database
        Parameters:
            - user_name: name of the user to check
        """
        for user in self.database["users"]:
            if user["user_name"] == user_name:
                return True

        return False

    def does_dataset_exists(self, dataset_name: str) -> bool:
        """
        Checks if dataset exist in the database
        Parameters:
            - dataset_name: name of the dataset to check
        """
        return dataset_name in self.database["datasets"]

    def may_user_query(self, user_name: str) -> bool:
        """
        Checks if a user may query the server.
        Cannot query if already querying.
        Parameters:
            - user_name: name of the user
        """
        if not (self.does_user_exists(user_name)):
            raise ValueError(
                f"User {user_name} does not exists. Cannot check access."
            )
        for user in self.database["users"]:
            if user["user_name"] == user_name:
                return user["may_query"]

    def set_may_user_query(self, user_name: str, may_query: bool) -> None:
        """
        Sets if a user may query the server.
        (Set False before querying and True after updating budget)
        Parameters:
            - user_name: name of the user
            - may_query: flag give or remove access to user
        """
        if not (self.does_user_exists(user_name)):
            raise ValueError(
                f"User {user_name} does not exists. Cannot check access."
            )

        users = self.database["users"]
        for user in users:
            if user["user_name"] == user_name:
                user["may_query"] = may_query
        self.database["users"] = users

    def has_user_access_to_dataset(
        self, user_name: str, dataset_name: str
    ) -> bool:
        """
        Checks if a user may access a particular dataset
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
        """
        if not (self.does_user_exists(user_name)):
            raise ValueError(
                f"User {user_name} does not exists. Cannot check access."
            )
        if not (self.does_dataset_exists(dataset_name)):
            raise ValueError(
                f"Dataset {dataset_name} does not exists. "
                "Cannot check access."
            )

        for user in self.database["users"]:
            if user["user_name"] == user_name:
                for dataset in user["datasets_list"]:
                    if dataset["dataset_name"] == dataset_name:
                        return True
        return False

    def get_epsilon_or_delta(
        self, user_name: str, dataset_name: str, parameter: str
    ) -> float:
        """
        Get the current epsilon or delta spent by a specific user
        on a specific dataset
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
            - parameter: current_epsilon or current_delta
        """
        if self.has_user_access_to_dataset(user_name, dataset_name):
            for user in self.database["users"]:
                if user["user_name"] == user_name:
                    for dataset in user["datasets_list"]:
                        if dataset["dataset_name"] == dataset_name:
                            return dataset[parameter]
        else:
            raise ValueError(
                f"{user_name} has no access to {dataset_name}. "
                "Cannot get any budget estimate."
            )

    def get_current_budget(
        self, user_name: str, dataset_name: str
    ) -> [float, float]:
        """
        Get the current epsilon and delta spent by a specific user
        on a specific dataset
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
        """
        return [
            self.get_epsilon_or_delta(
                user_name, dataset_name, "current_epsilon"
            ),
            self.get_epsilon_or_delta(
                user_name, dataset_name, "current_delta"
            ),
        ]

    def get_max_budget(
        self, user_name: str, dataset_name: str
    ) -> [float, float]:
        """
        Get the maximum epsilon and delta budget that can be spent by a user
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
        """
        return [
            self.get_epsilon_or_delta(user_name, dataset_name, "max_epsilon"),
            self.get_epsilon_or_delta(user_name, dataset_name, "max_delta"),
        ]

    def update_epsilon_or_delta(
        self,
        user_name: str,
        dataset_name: str,
        parameter: str,
        spent_value: float,
    ) -> None:
        """
        Update the current epsilon spent by a specific user
        with the last spent epsilon
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
            - parameter: current_epsilon or current_delta
            - spent_value: spending of epsilon or delta on last query
        """
        if self.has_user_access_to_dataset(user_name, dataset_name):
            users = self.database["users"]
            for user in users:
                if user["user_name"] == user_name:
                    for dataset in user["datasets_list"]:
                        if dataset["dataset_name"] == dataset_name:
                            dataset[parameter] += spent_value
            self.database["users"] = users
        else:
            raise ValueError(
                f"{user_name} has no access to {dataset_name}. "
                "Cannot update any budget estimate."
            )

    def update_epsilon(
        self, user_name: str, dataset_name: str, spent_epsilon: float
    ) -> None:
        """
        Update the current epsilon spent by a specific user
        with the last spent epsilon
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
            - spent_epsilon: value of epsilon spent on last query
        """
        return self.update_epsilon_or_delta(
            user_name, dataset_name, "current_epsilon", spent_epsilon
        )

    def update_delta(
        self, user_name: str, dataset_name: str, spent_delta: float
    ) -> None:
        """
        Update the current delta spent by a specific user
        with the last spent delta
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
            - spent_delta: value of delta spent on last query
        """
        self.update_epsilon_or_delta(
            user_name, dataset_name, "current_delta", spent_delta
        )

    def update_budget(
        self,
        user_name: str,
        dataset_name: str,
        spent_epsilon: float,
        spent_delta: float,
    ) -> None:
        """
        Update the current epsilon and delta spent by a specific user
        with the last spent budget
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
            - spent_epsilon: value of epsilon spent on last query
            - spent_delta: value of delta spent on last query
        """
        self.update_epsilon(user_name, dataset_name, spent_epsilon)
        self.update_delta(user_name, dataset_name, spent_delta)

    def save_query(
        self,
        user_name: str,
        dataset_name: str,
        epsilon: float,
        delta: float,
        query: dict,
    ) -> None:
        """
        Save queries of user on datasets in a separate json file
        Parameters:
            - user_name: name of the user
            - dataset_name: name of the dataset
            - epsilon: value of epsilon spent on last query
            - delta: value of delta spent on last query
            - query: json string of the query
        """
        self.queries_archives.append(
            {
                "user_name": user_name,
                "dataset_name": dataset_name,
                "epsilon": epsilon,
                "delta": delta,
                "query": query,
            }
        )

    def save_current_database(self) -> None:
        """
        Saves the current database with updated parameters in new yaml
        with the date and hour in the path
        Might be useful to verify state of DB during development
        """
        new_path = self.path.replace(
            ".yaml", f'{datetime.now().strftime("%m_%d_%Y__%H_%M_%S")}.yaml'
        )
        with open(new_path, "w") as file:
            yaml.dump(self.database, file)

    def save_current_archive_queries(self) -> None:
        """
        Saves the current list of queries in a JSON
        """
        with open(QUERIES_ARCHIVES, "w") as outfile:
            json.dump(self.queries_archives, outfile)
