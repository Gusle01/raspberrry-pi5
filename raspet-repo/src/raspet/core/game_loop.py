"""메인 게임 루프 (Pygame 기반)."""
from .. import config


class GameLoop:
    """게임 전체를 구동하는 메인 루프.

    Pygame으로 프레임을 그린 뒤 OLED로 전송하는 구조.
    """

    def __init__(self) -> None:
        self.running = False
        # TODO: pygame 초기화, Surface 생성, SceneManager 구성

    def run(self) -> None:
        """입력 처리 → 상태 갱신 → 렌더 → 출력 루프를 반복한다."""
        self.running = True
        while self.running:
            # TODO: 1) 입력 처리 (조이스틱/카메라/버튼)
            # TODO: 2) 현재 씬 업데이트
            # TODO: 3) 프레임 렌더링
            # TODO: 4) OLED로 프레임 전송
            # TODO: 5) FPS 제한 (config.FPS)
            break  # 골격 단계: 즉시 종료

    def stop(self) -> None:
        self.running = False
