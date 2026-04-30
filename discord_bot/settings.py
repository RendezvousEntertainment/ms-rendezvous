from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    A dataclass to contain settings for our bot.
    Uses pydantic: see https://docs.pydantic.dev/usage/settings/ for more info.
    """

    token: str
    name: str = "Discord Bot"
    domain: str = "https://git.rendezvous.dev"
    repo: str = "rendezvous-entertainment/ksp2redux"
    gitlab_token: str = ""

    @property
    def repo_url(self) -> str:
        return f"{self.domain}/{self.repo}"

    class Config:
        env_file = ".env"  # load from a .env file
        env_prefix = "BOT_"  # env vars are prefixed with BOT_
