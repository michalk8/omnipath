import json
from io import BytesIO
from typing import Any, Union, Mapping, Callable, Optional
from hashlib import md5
from urllib.parse import urljoin

from requests import Request, Session, PreparedRequest
from tqdm.auto import tqdm
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

import pandas as pd

from omnipath._options import options
from omnipath.constants import QueryType
from omnipath.constants._pkg_constants import _QueryTypeSummary, _OmnipathEndpoints


class Downloader:
    def __init__(self):
        self._session = Session()
        self._cacher = options.cache
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=options.num_retries,
                redirect=5,
                method_whitelist=["HEAD", "GET", "OPTIONS"],
                status_forcelist=[413, 429, 500, 502, 503, 504],
                backoff_factor=1,
            )
        )

        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def resources(self) -> Mapping[str, Mapping[str, Any]]:
        return self.maybe_download(
            urljoin(options.url, _OmnipathEndpoints.RESOURCES.value),
            callback=json.load,
        )

    def maybe_download(
        self,
        url: str,
        callback: Callable[[Any], BytesIO],
        params: Optional[Mapping[str, str]] = None,
        cache: bool = True,
        **_,
    ) -> Any:
        if callback is not None and not callable(callback):
            raise TypeError(
                f"Expected `callback` to be either `None` or `callable`, "
                f"found `{type(callback).__name__}`."
            )

        req = self._session.prepare_request(
            Request(
                "GET", url, params=params, headers={"User-agent": "omnipathdb-user"}
            )
        )
        key = md5(bytes(req.url, encoding="utf-8")).hexdigest()

        if key in self._cacher:
            res = self._cacher[key]
        else:
            res = callback(self._download(req))
            if cache:
                self._cacher[key] = res

        return res

    def _download(self, req: PreparedRequest) -> Any:
        handle = BytesIO()

        with self._session.send(req, stream=True, timeout=options.timeout) as resp:
            resp.raise_for_status()

            with tqdm(
                unit="B",
                unit_scale=True,
                miniters=1,
                unit_divisor=1024,
                total=len(resp.content),
            ) as t:
                for chunk in resp.iter_content(chunk_size=options.chunk_size):
                    handle.write(chunk)
                    t.update(len(chunk))

                handle.flush()
                handle.seek(0)

        return handle


def _strip_resource_labels(df: pd.DataFrame, inplace: bool = True):
    # TODO
    pass


def _format_url(url: str, query: Union[QueryType, _QueryTypeSummary]) -> str:
    if not isinstance(query, (QueryType, _QueryTypeSummary)):
        raise TypeError()

    return urljoin(url, query.value)
