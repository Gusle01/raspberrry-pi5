"""애플리케이션 부트스트랩.

하드웨어/디스플레이를 초기화하고 게임 루프를 시작한다.
"""
from . import config
from .core.game_loop import GameLoop


def main() -> None:
    """RasPet을 실행한다."""
    # TODO: 하드웨어 초기화 (display, joystick, ultrasonic, buzzer)
    # TODO: 저장 데이터 불러오기 (storage.save)
    game = GameLoop()
    game.run()


if __name__ == "__main__":
    main()
