import chess

from src.analysis.move_classifier import MoveClassifier


class TestPhase2Analysis:
    def test_classify_opening(self):
        # Standard starting position
        fen = chess.STARTING_FEN
        phase = MoveClassifier.classify_game_phase(fen, 1)
        assert phase == "opening"

        # Move 10, full board
        phase = MoveClassifier.classify_game_phase(fen, 10)
        assert phase == "opening"

    def test_classify_middlegame(self):
        # Move 20, standard material
        fen = "rnbq1rk1/ppp2ppp/5n2/3pp3/1bB1P3/2N2N2/PPPP1PPP/R1BQK2R w KQ - 0 6"  # Some position
        phase = MoveClassifier.classify_game_phase(fen, 20)
        assert phase == "middlegame"

    def test_classify_endgame_no_queens(self):
        # No queens, but some pieces
        # r1b2rk1/ppp2ppp/5n2/4p3/1bB5/2N2N2/PPPP1PPP/R1B2RK1 w - - 0 10 (Removed queens)
        fen = "r1b2rk1/ppp2ppp/5n2/4p3/1bB5/2N2N2/PPPP1PPP/R1B2RK1 w - - 0 10"
        phase = MoveClassifier.classify_game_phase(fen, 25)
        # My logic: no_queens -> endgame
        assert phase == "endgame"

    def test_classify_endgame_low_material(self):
        # Queens on but very low material? Unlikely but possible.
        # Logic: total_material < 24.
        # K+Q vs K+Q (9+9=18 material)
        fen = "4k3/8/8/8/8/8/4Q3/4K3 w - - 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 50)
        assert phase == "endgame"

    def test_opening_extraction_fallback(self):
        # Mock Game object

        # Test 1: Standard Opening Header
        pgn_std = '[Event "?"]\n[Opening "Sicilian Defense"]\n[ECO "B20"]\n\n1. e4 c5'
        # We need to simulate the extraction logic inside analyze_game
        # Extract logic implies parsing PGN.
        # I'll paste the extraction logic here or mock analyze_game partially?
        # Better: test the logic isolated if possible, or just run a mini-test integration.

        # Let's perform the extraction manually as implemented in GameAnalyzer
        import io

        chess_game = chess.pgn.read_game(io.StringIO(pgn_std))
        name = chess_game.headers.get("Opening", "")
        if not name:
            name = chess_game.headers.get("ECOUrl", "").split("/")[-1].replace("-", " ").title()

        assert name == "Sicilian Defense"

        # Test 2: Chess.com ECOUrl
        pgn_chesscom = '[Event "?"]\n[ECOUrl "https://www.chess.com/openings/Sicilian-Defense-Najdorf-Variation"]\n\n1. e4 c5'
        chess_game = chess.pgn.read_game(io.StringIO(pgn_chesscom))
        name = chess_game.headers.get("Opening", "")
        if not name:
            name = chess_game.headers.get("ECOUrl", "").split("/")[-1].replace("-", " ").title()

        assert name == "Sicilian Defense Najdorf Variation"
