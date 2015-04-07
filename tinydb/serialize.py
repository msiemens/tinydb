from abc import ABCMeta, abstractmethod, abstractproperty
from tinydb.utils import with_metaclass


class Serializer(with_metaclass(ABCMeta, object)):
    """
    The abstract base class for Serializers.

    Allows TinyDB to handle arbitrary objects by running them through a list
    of registerd serializers.

    Every serializer has to tell which class it can handle.
    """

    @abstractproperty
    def OBJ_CLASS(self):
        raise NotImplementedError('To be overriden!')

    @abstractmethod
    def encode(self, obj):
        """
        Encode an object.

        :param obj:
        :return:
        :rtype: str
        """
        raise NotImplementedError('To be overriden!')

    @abstractmethod
    def decode(self, s):
        """
        Decode an object.

        :param s:
        :type s: str
        :return:
        """
        raise NotImplementedError('To be overriden!')
