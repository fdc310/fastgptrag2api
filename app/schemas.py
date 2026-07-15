from pydantic import BaseModel
from typing import Optional, Any


# ---- generic ----

class ApiResponse(BaseModel):
    code: int = 200
    statusText: str = ""
    message: str = ""
    data: Optional[Any] = None


# ---- dataset ----

class DatasetCreate(BaseModel):
    name: str
    intro: Optional[str] = ""
    avatar: Optional[str] = ""
    parentId: Optional[str] = None
    type: Optional[str] = "dataset"
    vectorModel: Optional[str] = ""
    agentModel: Optional[str] = ""
    vlmModel: Optional[str] = ""


# ---- collection common params ----

class CollectionCommonParams(BaseModel):
    trainingType: str = "chunk"
    chunkSettingMode: Optional[str] = "auto"
    chunkSplitMode: Optional[str] = "size"
    chunkSize: Optional[int] = 1500
    indexSize: Optional[int] = 512
    chunkSplitter: Optional[str] = ""
    qaPrompt: Optional[str] = ""
    tags: Optional[list[str]] = []
    createTime: Optional[str] = None
    indexPrefixTitle: Optional[bool] = False
    customPdfParse: Optional[bool] = False
    autoIndexes: Optional[bool] = False
    imageIndex: Optional[bool] = False


class CollectionCreateFolder(BaseModel):
    name: str
    parentId: Optional[str] = None
    type: str = "virtual"
    metadata: Optional[dict] = {}


class CollectionCreateText(CollectionCommonParams):
    text: str
    name: str
    parentId: Optional[str] = None
    metadata: Optional[dict] = {}


class CollectionCreateLink(CollectionCommonParams):
    link: str
    parentId: Optional[str] = None
    metadata: Optional[dict] = {}


class CollectionCreateApi(CollectionCommonParams):
    name: str
    apiFileId: str
    parentId: Optional[str] = None


class CollectionUpdate(BaseModel):
    id: Optional[str] = None
    externalFileId: Optional[str] = None
    datasetId: Optional[str] = None
    parentId: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[list[str]] = None
    forbid: Optional[bool] = None
    createTime: Optional[str] = None


class CollectionListParams(BaseModel):
    offset: int = 0
    pageSize: int = 10
    parentId: Optional[str] = None
    searchText: Optional[str] = ""


class CollectionDelete(BaseModel):
    collectionIds: list[str]


# ---- data ----

class IndexItem(BaseModel):
    type: Optional[str] = "custom"
    dataId: Optional[str] = None
    text: str


class PushDataItem(BaseModel):
    q: str
    a: Optional[str] = ""
    indexes: Optional[list[IndexItem]] = []


class PushDataParams(BaseModel):
    collectionId: Optional[str] = None  # auto-filled from URL path, do not set manually
    trainingType: str = "chunk"
    prompt: Optional[str] = ""
    billId: Optional[str] = None
    data: list[PushDataItem]


class DataListParams(BaseModel):
    offset: int = 0
    pageSize: int = 10
    searchText: Optional[str] = ""


class DataUpdate(BaseModel):
    dataId: str
    q: Optional[str] = None
    a: Optional[str] = None
    indexes: Optional[list[IndexItem]] = None


# ---- search ----

class SearchTestParams(BaseModel):
    text: str
    limit: int = 5000
    similarity: float = 0
    searchMode: str = "embedding"
    usingReRank: bool = False
    datasetSearchUsingExtensionQuery: bool = False
    datasetSearchExtensionModel: Optional[str] = "gpt-4o-mini"
    datasetSearchExtensionBg: Optional[str] = ""
