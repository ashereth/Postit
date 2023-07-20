from dataclasses import dataclass, field
from datetime import datetime

#create a class that will be used for posts
@dataclass
class Post:
    _id: str
    title: str
    body: str
    #account obj is none as base for now
    account: object = None
    date: datetime = datetime.now
    #number of likes should always start as 0
    likes: int = 0
    liked_by: list[str] = field(default_factory=list)

@dataclass
class Account:
    _id: str
    email: str
    username: str
    password: str
    posts: list[str] = field(default_factory=list)
    follower: list[str] = field(default_factory=list)
    following: list[str] = field(default_factory=list)