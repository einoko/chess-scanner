import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from typing import List
import keras
import cv2
import numpy as np
import chess

board_size = 400
square_size = int(board_size / 8)

# Piece labels, lowercase for black, uppercase for white
onehot_labels = ["empty", "k", "q", "r", "b", "n", "p", "K", "Q", "R", "B", "N", "P"]

model = keras.models.load_model("chess_model.h5")


def restore_onehot(y_pred: np.ndarray) -> np.ndarray:
    y_pred = np.argmax(y_pred, axis=1)
    y_pred = np.array([onehot_labels[i] for i in y_pred])
    return y_pred


def construct_board(labels: List[str]) -> chess.Board:
    board = chess.Board()

    for square, pred_piece in zip(chess.SQUARES, labels):
        color = chess.WHITE if pred_piece.isupper() else chess.BLACK
        if pred_piece == "empty":
            board.remove_piece_at(square)
        elif pred_piece.lower() == "k":
            board.set_piece_at(square, chess.Piece(chess.KING, color))
        elif pred_piece.lower() == "q":
            board.set_piece_at(square, chess.Piece(chess.QUEEN, color))
        elif pred_piece.lower() == "r":
            board.set_piece_at(square, chess.Piece(chess.ROOK, color))
        elif pred_piece.lower() == "b":
            board.set_piece_at(square, chess.Piece(chess.BISHOP, color))
        elif pred_piece.lower() == "n":
            board.set_piece_at(square, chess.Piece(chess.KNIGHT, color))
        elif pred_piece.lower() == "p":
            board.set_piece_at(square, chess.Piece(chess.PAWN, color))

    return board


def extract_squares(image_data: np.ndarray) -> np.ndarray:
    squares = []

    # Split the image into 64 squares
    # We want to go through the squares in the order of A1, A2, A3, ..., H7, H8
    for i in range(7, -1, -1):
        for j in range(0, 8):
            square = image_data[
                i * int(board_size / 8) : (i + 1) * int(board_size / 8),
                j * int(board_size / 8) : (j + 1) * int(board_size / 8),
            ]
            squares.append(square.flatten())

    return np.array(squares).reshape(-1, square_size, square_size, 3) / 255.0


def set_below_confidence_to_empty(
    y_pred: np.ndarray, y_labels: list, confidence: float
) -> list:
    y_max = np.amax(y_pred, axis=1)
    y_dict = {}

    for i in range(0, 64):
        y_dict[chess.SQUARES[i]] = (y_labels[i], y_max[i])

    for square, (_, prob) in y_dict.items():
        if prob < confidence:
            y_dict[square] = ("empty", 1.0)

    return [x[0] for x in y_dict.values()]


def parse_board(image_data: bytes, color: str) -> chess.Board:
    # Read the image and resize it to 400×400
    photo = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    photo = cv2.resize(photo, (board_size, board_size), interpolation=cv2.INTER_AREA)

    # Extract the squares from the image, (reshape & normalize) for the model
    squares = extract_squares(photo)

    # Predict the piece in each square
    y_pred = model.predict(squares, verbose=0)

    # Convert the one-hot encoded predictions back to the original labels
    y_labels = restore_onehot(y_pred)

    # Heuristics to fix possible errors
    # If the model is not confident (95% or more) about a square, set it to empty
    y_labels = set_below_confidence_to_empty(y_pred, y_labels, 0.95)

    board = construct_board(y_labels)

    # If the board is from the perspective of black, flip it
    if color == "black":
        board = board.transform(chess.flip_vertical).transform(chess.flip_horizontal)

    return board


def get_fen(image_data: bytes, color: str) -> str:
    image_buffer = np.frombuffer(image_data, np.uint8)
    try:
        board = parse_board(image_buffer, color)

        # Only include piece placement in the FEN
        fen = board.fen().split(" ")[0]

        return fen
    except Exception as e:
        print(e)
        return ""


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python chess_eye.py <path_to_image> <color>")
        sys.exit(1)

    image_path = sys.argv[1]
    color = sys.argv[2]

    image_data = open(image_path, "rb").read()

    fen = get_fen(image_data, color)

    print(fen)
