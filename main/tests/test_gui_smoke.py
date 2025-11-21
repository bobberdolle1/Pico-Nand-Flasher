import pytest


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_gui_smoke(qtbot):
    # Lazy import to ensure PyQt6 is available
    from src.gui.gui_interface import NANDFlasherGUI

    gui = NANDFlasherGUI()
    qtbot.addWidget(gui.root)

    # Basic assertions on constructed widgets
    assert gui.root.windowTitle()
    assert gui.status_label is not None

    # Simulate minimal lifecycle
    gui.status_label.config(text="Testing...")
    assert gui.status_label.cget("text") == "Testing..."

    # Close the window to cleanup
    gui.root.destroy()
