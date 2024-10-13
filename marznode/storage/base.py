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
    async def remove_user(self, user: User) -> None:
        """
        removes a user and all the inbounds
        :param user: the user
        :return: nothing
        """

    @abstractmethod
    async def flush_users(self) -> None:
        """
        removes all users
        :return: nothing
        """

    @abstractmethod
    async def list_inbound_users(self, tag: str) -> list[User]:
        """returns a list of users subscribed to an inbound"""

    @abstractmethod
    def register_inbound(self, inbound: Inbound) -> None:
        """
        registers a new inbound
        :param inbound: the inbound to register
        :return: nothing
        """

    def remove_inbound(self, inbound: Inbound | str) -> None:
        """
        removes an inbound
        :param inbound: the inbound to remove
        :return: nothing
        """
