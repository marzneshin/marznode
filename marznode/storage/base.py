"""The base for marznode storage"""
from abc import ABC, abstractmethod


class BaseStorage(ABC):
    """Base class for marznode storage"""
    @abstractmethod
    async def list_users(self, user_id: int | None = None) -> list[dict] | dict:
        """
        lists users in the storage
        :param user_id: if specified only one or no user(s) will be returned
        :return: a list of users or the user specified
        """

    @abstractmethod
    async def list_inbounds(self, tag: list[str] | str | None = None,
                            include_users: bool = False) -> list[dict] | dict:
        """
        lists all inbounds or the one specified by tag
        :param tag: specify one or more tags
        :param include_users: includes users if set to true
        :return: list of all inbounds or the one specified
        """

    @abstractmethod
    async def update_user_inbounds(self, user_id: int, inbounds: list[str]) -> None:
        """
        removes all previous inbound tags from the user and sets them to inbounds
        :param user_id: the user
        :param inbounds: list of the inbounds
        :return: nothing
        """

    @abstractmethod
    async def repopulate_users(self, users: list[dict]) -> None:
        """
        removes all users and adds the ones specified
        :param users: list of users to add
        :return: nothing
        """

    @abstractmethod
    async def add_user(self, user: dict, inbounds: list[str]) -> None:
        """
        adds a user
        :param user: the user
        :param inbounds: list of inbound tags
        :return: nothing
        """

    async def remove_user(self, user_id: int) -> None:
        """
        removes a user and all the inbounds
        :param user_id: the user's id
        :return: nothing
        """

    def set_inbounds(self, inbounds: dict[str, dict]) -> None:
        """
        resets all inbounds
        :param inbounds: inbounds
        :return: nothing
        """
