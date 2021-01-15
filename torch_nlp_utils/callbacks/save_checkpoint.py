from typing import Dict, Any
import os
import json
import torch
import shutil
from loguru import logger


class SaveCheckpoint:
    """
    Save PyTorch Model after each epoch.

    Parameters
    ----------
    model : `torch.nn.Module`, required
        Torch model to monitor.
    directory : `str`, required
        Directory to save model checkpoints per epoch.
    keep_num_checkpoints : `int`, optional (default = `None`)
        Number of checkpoints to keep. If None then keep all of them.
    """

    def __init__(
        self,
        directory: str,
        model: torch.nn.Module = None,
        keep_num_checkpoints: int = None,
    ) -> None:
        if model is None:
            logger.warning(
                "Model is not passed in init. "
                "Then you should pass dict to save with torch.save by yourself."
            )
        os.makedirs(directory, exist_ok=False)
        if keep_num_checkpoints is not None and keep_num_checkpoints < 1:
            raise Exception("keep_num_checkpoints should be greater than 0")
        self.epoch_idx = 0
        self._model = model
        self._directory = directory
        self._keep_num_checkpoints = keep_num_checkpoints
        self._best_model_path = None

    @property
    def best_model_path(self) -> str:
        return self._best_model_path

    def __call__(
        self,
        metrics: Dict[str, Any],
        is_best_so_far: bool,
        save_dict: Dict[str, Any] = None
    ) -> None:
        """Perform saving after one epoch."""
        if not save_dict and not self._model:
            raise Exception("You should pass save_dict on call if model is None.")
        cur_epoch_dir = os.path.join(self._directory, f"epoch_{self.epoch_idx}")
        os.makedirs(cur_epoch_dir, exist_ok=True)
        # Save torch model
        torch.save(save_dict or self._model.state_dict(), os.path.join(cur_epoch_dir, "model.pt"))
        # Save metrics
        with open(os.path.join(cur_epoch_dir, "metrics.json"), mode="w", encoding="utf-8") as file:
            json.dump(metrics, file, ensure_ascii=False, indent=2)
        # Save best model
        if is_best_so_far:
            logger.info(
                f"Best validation performance so far. Copying to '{self._directory}/best'.",
            )
            best_model_path = os.path.join(self._directory, "best")
            shutil.copytree(cur_epoch_dir, best_model_path)
            self._best_model_path = best_model_path
        # Delete spare checkpoints
        if self._keep_num_checkpoints:
            self._delete_spare_if_needed()
        # Update epoch index
        self.epoch_idx += 1

    def _delete_spare_if_needed(self):
        checkpoints = sorted(os.listdir(self._directory))
        if len(checkpoints) > self._keep_num_checkpoints:
            for checkpoint in checkpoints[:-self._keep_num_checkpoints]:
                shutil.rmtree(os.path.join(self._directory, checkpoint), ignore_errors=True)
