import sys
import re
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QFileDialog,
    QTextEdit, QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pypdf import PdfReader, PdfWriter


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_")
    return name[:100]


def get_bookmarks_flat(outline, reader, depth=0, max_depth=1):
    results = []
    for item in outline:
        if isinstance(item, list):
            if depth < max_depth:
                results.extend(get_bookmarks_flat(item, reader, depth + 1, max_depth))
        else:
            try:
                page_num = reader.get_destination_page_number(item)
                results.append({"title": item.title, "page": page_num, "depth": depth})
            except Exception:
                pass
    return results


class SplitWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_path, output_dir, max_depth):
        super().__init__()
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.max_depth = max_depth

    def run(self):
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            reader = PdfReader(str(self.input_path))
            total_pages = len(reader.pages)
            self.log.emit(f"📄 File: {self.input_path.name} ({total_pages} trang)")

            if not reader.outline:
                self.error.emit("⚠️ File này không có bookmark.")
                return

            bookmarks = get_bookmarks_flat(reader.outline, reader, max_depth=self.max_depth)
            if not bookmarks:
                self.error.emit("⚠️ Không tìm thấy bookmark nào ở depth được chỉ định.")
                return

            bookmarks.sort(key=lambda x: x["page"])
            self.log.emit(f"\n📑 Tìm thấy {len(bookmarks)} bookmark:\n")

            for i, bm in enumerate(bookmarks):
                end = bookmarks[i + 1]["page"] - 1 if i + 1 < len(bookmarks) else total_pages - 1
                self.log.emit(f"  [{i+1:02d}] Trang {bm['page']+1:>4} → {end+1:>4}  |  {bm['title']}")

            self.log.emit(f"\n✂️ Đang split và lưu vào: {self.output_dir}\n")

            for i, bm in enumerate(bookmarks):
                start_page = bm["page"]
                end_page = bookmarks[i + 1]["page"] - 1 if i + 1 < len(bookmarks) else total_pages - 1

                writer = PdfWriter()
                for p in range(start_page, end_page + 1):
                    writer.add_page(reader.pages[p])

                safe_title = sanitize_filename(bm["title"])
                filename = f"{i+1:02d}_{safe_title}.pdf"
                out_path = self.output_dir / filename

                with open(out_path, "wb") as f:
                    writer.write(f)

                page_count = end_page - start_page + 1
                self.log.emit(f"  ✅ {filename}  ({page_count} trang)")
                self.progress.emit(int((i + 1) / len(bookmarks) * 100))

            self.log.emit(f"\n🎉 Hoàn thành! {len(bookmarks)} file được lưu trong: {self.output_dir}")
            self.finished.emit()
        except Exception as e:
            self.error.emit(f"❌ Lỗi: {e}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Split PDF by Bookmark")
        self.setMinimumWidth(600)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Input file ---
        input_group = QGroupBox("File PDF đầu vào")
        input_layout = QHBoxLayout(input_group)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Chọn file PDF...")
        btn_browse_input = QPushButton("Browse...")
        btn_browse_input.clicked.connect(self._browse_input)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(btn_browse_input)
        layout.addWidget(input_group)

        # --- Output dir ---
        output_group = QGroupBox("Thư mục output")
        output_layout = QHBoxLayout(output_group)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Mặc định: <tên_file>_chapters/")
        btn_browse_output = QPushButton("Browse...")
        btn_browse_output.clicked.connect(self._browse_output)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(btn_browse_output)
        layout.addWidget(output_group)

        # --- Depth ---
        depth_group = QGroupBox("Cài đặt")
        depth_layout = QHBoxLayout(depth_group)
        depth_layout.addWidget(QLabel("Bookmark depth:"))
        self.depth_spin = QSpinBox()
        self.depth_spin.setMinimum(0)
        self.depth_spin.setMaximum(10)
        self.depth_spin.setValue(0)
        self.depth_spin.setToolTip("0 = chỉ top-level, 1 = cả sub-chapter, ...")
        depth_layout.addWidget(self.depth_spin)
        depth_layout.addStretch()
        layout.addWidget(depth_group)

        # --- Run button + progress ---
        self.btn_run = QPushButton("▶  Split PDF")
        self.btn_run.setFixedHeight(36)
        self.btn_run.clicked.connect(self._run)
        layout.addWidget(self.btn_run)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- Log ---
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(200)
        layout.addWidget(self.log_box)

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file PDF", "", "PDF Files (*.pdf)")
        if path:
            self.input_edit.setText(path)
            # Auto-fill output dir
            if not self.output_edit.text():
                default_out = str(Path(path).parent / (Path(path).stem + "_chapters"))
                self.output_edit.setText(default_out)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục output")
        if path:
            self.output_edit.setText(path)

    def _run(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            self.log_box.append("❌ Vui lòng chọn file PDF đầu vào.")
            return

        output_dir = self.output_edit.text().strip() or None
        if output_dir is None:
            output_dir = str(Path(input_path).parent / (Path(input_path).stem + "_chapters"))

        self.log_box.clear()
        self.progress_bar.setValue(0)
        self.btn_run.setEnabled(False)

        self.worker = SplitWorker(input_path, output_dir, self.depth_spin.value())
        self.worker.log.connect(self.log_box.append)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(lambda: self.btn_run.setEnabled(True))
        self.worker.error.connect(lambda msg: (self.log_box.append(msg), self.btn_run.setEnabled(True)))
        self.worker.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())