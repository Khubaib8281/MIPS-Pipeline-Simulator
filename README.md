# MIPS Pipeline Simulator

An interactive **MIPS 5-stage pipeline simulator** for visualizing pipeline execution, datapaths, hazards, and control signals. This tool is designed for students, educators, and enthusiasts to **understand CPU pipeline execution**, instruction hazards, and performance metrics like **CPI and stalls**.

---

## Features

- **5-Stage Pipeline Simulation**
  - Instruction Fetch (IF)
  - Instruction Decode / Register Read (ID)
  - Execute / ALU (EX)
  - Memory Access (MEM)
  - Write Back (WB)

- **Instruction Support**
  - Arithmetic: `ADD`, `SUB`, `MUL`
  - Immediate: `ADDI`, `ORI`, `LUI`, `LI`
  - Memory: `LW`, `SW`, `LB`, `LH`
  - Branch: `BEQ`
  - Handles NOPs and invalid instructions gracefully

- **Pipeline Hazards**
  - Load-Use Hazard
  - RAW (Read After Write) Hazard
  - Instruction errors are highlighted dynamically

- **Forwarding Support**
  - Enable/disable **data forwarding** to reduce stalls

- **Control Signals Visualization**
  - RegWrite, MemRead, MemWrite, ALUSrc, Branch
  - Signals are dynamically updated per instruction in EX stage

- **Datapath Visualization**
  - Full 5-stage datapath
  - Active stages highlighted in **red**
  - Forwarding paths shown when enabled

- **Performance Metrics**
  - Cycle count
  - Stalls count
  - CPI (Cycles Per Instruction)

- **Interactive Interface**
  - Step through instructions cycle by cycle
  - Run program automatically
  - Reset pipeline at any time
  - Editable assembly code in the UI

---

## Built With

- [Python 3](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — for interactive web UI
- [Graphviz](https://graphviz.org/) — for pipeline and datapath diagrams

---

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/Khubaib8281/mips-pipeline-simulator.git
cd mips-pipeline-simulator
```

2. **Install dependencies:**

```bash
pip install streamlit graphviz
```

3. **Run the simulator:**

```bash
streamlit run app.py
```

> Open your browser at `http://localhost:8501` to use the simulator.

---

## Usage

1. **Enter MIPS assembly code** in the left panel.
2. **Enable or disable forwarding** to see how it affects hazards.
3. **Step through cycles** using the ▶ Next Cycle button.
4. **Run the entire program** with ⏩ Run Program.
5. **Reset** pipeline to start fresh with 🔄 Reset.
6. **View Registers, Control Signals, and Pipeline Timeline** dynamically.
7. **Observe the datapath** and active stages in real-time.

---

## Visualization

- **Pipeline View:** Shows IF, ID, EX, MEM, WB stages with hazards highlighted.
- **Datapath View:** Full 5-stage datapath where active stages are highlighted in red, and forwarding paths are shown.

---

## Notes

- Only supports **32-bit integer operations**.
- Memory is limited to **256 words**.
- `$zero` is read-only and always contains 0.
- Instructions must follow standard **MIPS syntax**.

---

## Author

**Muhammad Khubaib Ahmad**  
AI/ML Engineer 
[GitHub](https://github.com/Khubaib8281) | [LinkedIn](https://www.linkedin.com/in/muhammad-khubaib-ahmad-)

---

## 📚 Learning Outcomes

This project is perfect for learning:

- CPU pipeline architecture and execution
- Data hazards and control hazards
- Forwarding and stalling techniques
- Pipeline performance metrics (CPI, stalls)
- Visual debugging of assembly programs

---

## 🌟 Future Enhancements

- Expand **supported instructions** (e.g., `J`, `JAL`, `SLT`, `AND`, `OR`, `XOR`)
- Dynamic **memory visualization** for full 256 addresses
- Advanced hazard types: **control hazards, branch prediction**
- Interactive **tutorial mode** for teaching pipeline concepts