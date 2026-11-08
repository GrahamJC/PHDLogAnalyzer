import contextlib
import io
import math
import os
import sys
import tkinter as tk
from dataclasses import fields
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from phdlogfile import CalibrateDirection, CalibrateSection, GuideSection, PHDLogFile

# Header fields not shown in the summary table (displayed elsewhere)
LIST_FIELDS = {"steps", "results", "infos"}

DIRECTION_COLOURS = {
    CalibrateDirection.West: "tab:blue",
    CalibrateDirection.East: "tab:cyan",
    CalibrateDirection.Backlash: "tab:gray",
    CalibrateDirection.North: "tab:red",
    CalibrateDirection.South: "tab:orange",
}


def rms(values):
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else 0.0


class App(tk.Tk):

    def __init__(self, path=None):
        super().__init__()
        self.title("PHD2 Log Analyser")
        self.geometry("1200x800")
        self.logFile = None

        self._buildMenu()
        self._buildToolbar()
        self._buildBody()
        self._buildStatusBar()

        if path:
            self.after_idle(self.openFile, path)

    # ---- layout ----

    def _buildMenu(self):
        menubar = tk.Menu(self)
        fileMenu = tk.Menu(menubar, tearoff=False)
        fileMenu.add_command(label="Open...", accelerator="Ctrl+O", command=self.browse)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=fileMenu)
        self.config(menu=menubar)
        self.bind_all("<Control-o>", lambda e: self.browse())

    def _buildToolbar(self):
        bar = ttk.Frame(self, padding=4)
        bar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(bar, text="Open log...", command=self.browse).pack(side=tk.LEFT)
        self.pathVar = tk.StringVar(value="No file loaded")
        ttk.Label(bar, textvariable=self.pathVar).pack(side=tk.LEFT, padx=8)

    def _buildBody(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Section list
        left = ttk.Frame(paned)
        self.sectionTree = ttk.Treeview(left, columns=("type", "start", "steps"), show="headings", selectmode="browse")
        for col, text, width in (("type", "Type", 90), ("start", "Start", 140), ("steps", "Steps", 60)):
            self.sectionTree.heading(col, text=text)
            self.sectionTree.column(col, width=width, stretch=False)
        self.sectionTree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._addScrollbar(left, self.sectionTree)
        self.sectionTree.bind("<<TreeviewSelect>>", lambda e: self.showSelectedSection())
        paned.add(left, weight=0)

        # Detail tabs
        self.tabs = ttk.Notebook(paned)
        paned.add(self.tabs, weight=1)

        self.chartFrame = ttk.Frame(self.tabs)
        self.figure = Figure(figsize=(8, 6), layout="constrained")
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chartFrame)
        NavigationToolbar2Tk(self.canvas, self.chartFrame).update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.tabs.add(self.chartFrame, text="Chart")

        # Guiding chart series toggles; only shown while a guiding section is displayed
        self.guideControls = ttk.Frame(self.chartFrame, padding=(4, 2))
        self.showRA = tk.BooleanVar(value=True)
        self.showDec = tk.BooleanVar(value=True)
        self.showCorrections = tk.BooleanVar(value=True)
        for text, var in (("RA", self.showRA), ("Dec", self.showDec), ("Corrections", self.showCorrections)):
            ttk.Checkbutton(self.guideControls, text=text, variable=var,
                            command=self._updateGuideVisibility).pack(side=tk.LEFT, padx=4)
        self.guideArtists = None

        self.summaryTree = self._addTableTab("Summary")
        self.stepsTree = self._addTableTab("Steps")
        self.infoTree = self._addTableTab("Info")
        self.logInfoTree = self._addTableTab("Log Info")

    def _buildStatusBar(self):
        self.statusVar = tk.StringVar()
        ttk.Label(self, textvariable=self.statusVar, relief=tk.SUNKEN, anchor=tk.W, padding=2).pack(side=tk.BOTTOM, fill=tk.X)

    def _addTableTab(self, title):
        frame = ttk.Frame(self.tabs)
        tree = ttk.Treeview(frame, show="headings")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._addScrollbar(frame, tree)
        self.tabs.add(frame, text=title)
        return tree

    @staticmethod
    def _addScrollbar(parent, tree):
        sb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=sb.set)

    @staticmethod
    def _fillTable(tree, columns, rows):
        tree.delete(*tree.get_children())
        tree["columns"] = columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=max(60, 8 * len(col)), stretch=True)
        for row in rows:
            tree.insert("", tk.END, values=row)

    # ---- actions ----

    def browse(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Open PHD2 guide log",
            filetypes=[("PHD2 logs", "*.txt *.log"), ("All files", "*.*")],
        )
        if path:
            self.openFile(path)

    def openFile(self, path):
        self.config(cursor="watch")
        self.update_idletasks()
        unmatched = io.StringIO()
        try:
            # The parser reports unmatched lines on stdout; capture them for the status bar
            with contextlib.redirect_stdout(unmatched):
                logFile = PHDLogFile(path)
        except Exception as e:
            messagebox.showerror("Open failed", f"Could not parse {path}:\n\n{type(e).__name__}: {e}", parent=self)
            return
        finally:
            self.config(cursor="")

        self.logFile = logFile
        self.pathVar.set(os.path.abspath(path))
        self.title(f"PHD2 Log Analyser - {os.path.basename(path)}")
        unmatchedCount = len(unmatched.getvalue().splitlines())
        self.statusVar.set(
            f"PHD2 {logFile.version}  |  {len(logFile.sections)} sections  |  {unmatchedCount} unmatched lines"
        )

        self.sectionTree.delete(*self.sectionTree.get_children())
        for i, section in enumerate(logFile.sections):
            kind = "Calibration" if isinstance(section, CalibrateSection) else "Guiding"
            self.sectionTree.insert("", tk.END, iid=str(i), values=(kind, f"{section.date} {section.time}", len(section.steps)))

        self._fillTable(self.logInfoTree, ("Line", "Info"), [(i.lineno, i.text) for i in logFile.infos])

        if logFile.sections:
            self.sectionTree.selection_set("0")
        else:
            self.clearSection()

    def clearSection(self):
        for tree in (self.summaryTree, self.stepsTree, self.infoTree):
            self._fillTable(tree, (), [])
        self.figure.clear()
        self.canvas.draw_idle()

    def showSelectedSection(self):
        selection = self.sectionTree.selection()
        if not selection:
            return
        section = self.logFile.sections[int(selection[0])]

        self._fillTable(
            self.summaryTree,
            ("Field", "Value"),
            [(f.name, getattr(section, f.name)) for f in fields(section) if f.name not in LIST_FIELDS],
        )

        if section.steps:
            stepFields = [f.name for f in fields(section.steps[0])]
            rows = [
                tuple(v.name if isinstance(v, CalibrateDirection) else v for v in (getattr(s, n) for n in stepFields))
                for s in section.steps
            ]
            self._fillTable(self.stepsTree, stepFields, rows)
        else:
            self._fillTable(self.stepsTree, (), [])

        self._fillTable(self.infoTree, ("Line", "Info"), [(i.lineno, i.text) for i in section.infos])

        self.figure.clear()
        if isinstance(section, GuideSection):
            self._plotGuide(section)
            self.guideControls.pack(side=tk.TOP, fill=tk.X, before=self.canvas.get_tk_widget())
            self._updateGuideVisibility()
        else:
            self.guideArtists = None
            self.guideControls.pack_forget()
            self._plotCalibration(section)
        self.canvas.draw_idle()

    # ---- charts ----

    def _plotGuide(self, section: GuideSection):
        good = [s for s in section.steps if s.err == 0]
        scale = section.pixelScale or 1.0
        units = '"' if section.pixelScale else "px"
        ra = [s.raraw * scale for s in good]
        dec = [s.decraw * scale for s in good]

        raRms, decRms = rms(ra), rms(dec)
        totalRms = math.hypot(raRms, decRms)
        dropped = len(section.steps) - len(good)

        # Frames with an error code (star lost etc.) become NaN so the line breaks across them
        t = [s.time for s in section.steps]
        raLine = [s.raraw * scale if s.err == 0 else math.nan for s in section.steps]
        decLine = [s.decraw * scale if s.err == 0 else math.nan for s in section.steps]

        # Correction pulses, signed to match the logged guide distances (W/S positive, E/N negative)
        raPulse = [s.radur if s.raDir == "W" else -s.radur for s in section.steps]
        decPulse = [s.decdur if s.decDir == "S" else -s.decdur for s in section.steps]

        axErr, axScatter = self.figure.subplots(1, 2, width_ratios=(3, 1))
        # Leave room between the plots for the correction axis labels
        self.figure.get_layout_engine().set(wspace=0.08)

        # Corrections on a secondary axis, drawn behind the error lines
        axPulse = axErr.twinx()
        axErr.set_zorder(axPulse.get_zorder() + 1)
        axErr.patch.set_visible(False)
        raBars = axPulse.vlines(t, 0, raPulse, color="tab:blue", alpha=0.35, linewidth=1.5, label="RA correction")
        decBars = axPulse.vlines(t, 0, decPulse, color="tab:red", alpha=0.35, linewidth=1.5, label="Dec correction")
        axPulse.set_ylabel("Correction (ms)")

        # Symmetric limits so zero lines up on both axes
        errMax = max((abs(v) for v in ra + dec), default=1.0) * 1.05 or 1.0
        pulseMax = max((abs(v) for v in raPulse + decPulse), default=1) * 1.05 or 1.0
        axErr.set_ylim(-errMax, errMax)
        axPulse.set_ylim(-pulseMax, pulseMax)

        [raPlot] = axErr.plot(t, raLine, color="tab:blue", linewidth=0.8, label=f"RA  (RMS {raRms:.2f}{units})")
        [decPlot] = axErr.plot(t, decLine, color="tab:red", linewidth=0.8, label=f"Dec (RMS {decRms:.2f}{units})")
        axErr.axhline(0, color="black", linewidth=0.5)
        axErr.set_xlabel("Time (s)")
        axErr.set_ylabel(f"Raw distance ({units})")
        axErr.set_title(
            f"Guiding {section.date} {section.time}\n"
            f"Total RMS {totalRms:.2f}{units}, {len(good)} frames, {dropped} dropped",
            fontsize=10,
        )
        axErr.grid(alpha=0.3)
        self.guideArtists = {
            "axErr": axErr, "axPulse": axPulse,
            "raPlot": raPlot, "decPlot": decPlot, "raBars": raBars, "decBars": decBars,
        }

        axScatter.scatter(ra, dec, s=3, alpha=0.4)
        axScatter.axhline(0, color="black", linewidth=0.5)
        axScatter.axvline(0, color="black", linewidth=0.5)
        axScatter.set_aspect("equal", adjustable="datalim")
        axScatter.set_xlabel(f"RA ({units})")
        axScatter.set_ylabel(f"Dec ({units})")
        axScatter.set_title("Scatter")
        axScatter.grid(alpha=0.3)

    def _updateGuideVisibility(self):
        a = self.guideArtists
        if a is None:
            return
        ra, dec, corrections = self.showRA.get(), self.showDec.get(), self.showCorrections.get()

        # A correction series is shown only when its axis is also enabled
        a["raPlot"].set_visible(ra)
        a["decPlot"].set_visible(dec)
        a["raBars"].set_visible(ra and corrections)
        a["decBars"].set_visible(dec and corrections)
        a["axPulse"].set_visible(corrections)

        visible = [h for h in (a["raPlot"], a["decPlot"], a["raBars"], a["decBars"]) if h.get_visible()]
        if visible:
            a["axErr"].legend(visible, [h.get_label() for h in visible], loc="upper right")
        elif a["axErr"].get_legend():
            a["axErr"].get_legend().remove()
        self.canvas.draw_idle()

    def _plotCalibration(self, section: CalibrateSection):
        ax = self.figure.subplots()
        for direction in CalibrateDirection:
            steps = [s for s in section.steps if s.direction == direction]
            if steps:
                ax.plot([s.x for s in steps], [s.y for s in steps], marker="o", markersize=3,
                        color=DIRECTION_COLOURS[direction], label=direction.name)
        ax.set_aspect("equal", adjustable="datalim")
        ax.invert_yaxis()  # image coordinates
        ax.set_xlabel("x (px)")
        ax.set_ylabel("y (px)")
        results = ", ".join(f"{r.direction.name} {r.angle:.1f}° @ {r.rate:.3f} px/s" for r in section.results)
        ax.set_title(f"Calibration {section.date} {section.time}\n{results}", fontsize=9)
        ax.legend()
        ax.grid(alpha=0.3)


def main():
    App(sys.argv[1] if len(sys.argv) > 1 else None).mainloop()


if __name__ == "__main__":
    main()
