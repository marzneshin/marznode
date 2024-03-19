"""The base for marznode storage"""

from abc import ABC, abstractmethod

from marznode.models import Inbound, User


class BaseStorage(ABC):
    """Base class for marznode storage"""

    @abstractmethod
    async def list_users(self, user_id: int | None = None) -> list[User] | User:
        """
        lists users in the storage
        :param user_id: if specified only one or no user(s) will be returned
        :return: a list of users or the user specified
        """

    @abstractmethod
    async def list_inbounds(
        self, tag: list[str] | str | None = None, include_users: bool = False
    ) -> list[Inbound] | Inbound:
        """
        lists all inbounds or the one specified by tag
        :param tag: specify one or more tags
        :param include_users: includes users if set to true
        :return: list of all inbounds or the one specified
        """

    @abstractmethod
    async def update_user_inbounds(self, user: User, inbounds: list[Inbound]) -> None:
        """
        removes all previous inbound tags from the user and sets them to inbounds
        :param user: the user
        :param inbounds: list of inbounds to be set
        :return: nothing
        """

    @abstractmethod
    async def remove_user(self, user_id: int) -> None:
        """
        removes a user and all the inbounds
        :param user_id: the user's id
        :return: nothing
        """

    @abstractmethod
    async def flush_users(self) -> None:
        """
        removes all users
        :return: nothing
        """

    @abstractmethod
    def set_inbounds(self, inbounds: dict[str, dict]) -> None:
        """
        resets all inbounds
        :param inbounds: inbounds
        :return: nothing
        """
