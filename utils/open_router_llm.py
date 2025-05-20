import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.utils.utils import secret_from_env
from langchain_openai import ChatOpenAI
from pydantic import Field, SecretStr

load_dotenv()


class ChatOpenRouter(ChatOpenAI):
    openai_api_key: Optional[SecretStr] = Field(
        alias="api_key",
        default_factory=secret_from_env("OPENROUTER_API_KEY", default=None),
    )

    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"openai_api_key": "OPENROUTER_API_KEY"}

    def __init__(self, openai_api_key: Optional[str] = None, **kwargs):
        openai_api_key = openai_api_key or os.environ.get("OPENROUTER_API_KEY")
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            openai_api_key=openai_api_key,
            **kwargs,
        )


if __name__ == "__main__":
    # Test the ChatOpenRouter
    try:
        openrouter_model = ChatOpenRouter(model_name="meta-llama/llama-4-maverick:free")
        response = openrouter_model.invoke("What is 2+2?")
        print("\nTest Response:")
        print("-------------")
        print(response.content)
        print("\nTest successful! ChatOpenRouter is working correctly.")
    except Exception as e:
        print("\nError testing ChatOpenRouter:")
        print("---------------------------")
        print(f"Error: {str(e)}")
        print("\nPlease check your OPENROUTER_API_KEY in the .env file.")
