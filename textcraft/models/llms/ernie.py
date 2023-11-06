import json
from typing import Any, List, Optional

import requests
from langchain.cache import InMemoryCache
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.globals import set_llm_cache
from langchain.llms.base import LLM

from textcraft.core.user_config import get_config

set_llm_cache(InMemoryCache())


class Ernie(LLM):
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        content = self._post(prompt)
        return content

    @property
    def _llm_type(self) -> str:
        return "Ernie"

    def _post(self, prompt):
        url = (
            "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token="
            + self._get_access_token()
        )
        payload = json.dumps(
            {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": float(get_config("settings.config.TEMPERATURE")),
            }
        )
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        print("=======>" + response.text)
        return json.loads(response.text)["result"]

    def _get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        API_KEY = get_config("settings.models.ERNIE.ERNIE_API_KEY")
        SECRET_KEY = get_config("settings.models.ERNIE.ERNIE_API_SECRET")
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": API_KEY,
            "client_secret": SECRET_KEY,
        }
        return str(requests.post(url, params=params).json().get("access_token"))
