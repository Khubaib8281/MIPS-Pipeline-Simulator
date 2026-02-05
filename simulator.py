import streamlit as st
import graphviz

# ----------------- REGISTER SET -----------------
def init_registers():
    regs = {
        "$zero": 0, "$ra": 0, "$sp": 0, "$fp": 0, "$gp": 0,
        "$v0": 0, "$v1": 0
    }
    for i in range(4):
        regs[f"$a{i}"] = 0
    for i in range(10):
        regs[f"$t{i}"] = 0
    for i in range(8):
        regs[f"$s{i}"] = 0
    return regs

# ----------------- DATAPATH GRAPH -----------------
def draw_datapath(pipe):
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="LR", size="10")
    dot.attr(size="12,8")
    
    # ---------- Define colors ----------
    default_color = "black"
    active_color = "red" if pipe.hazard_detected else "blue"
    
    # Highlight stage currently active in EX
    stage_colors = {
        "IF": default_color,
        "ID": default_color,
        "EX": default_color,
        "MEM": default_color,
        "WB": default_color
    }
    # Determine which stage is active
    # If there's a hazard, highlight the ID stage
    if pipe.hazard_detected:
        stage_colors["ID"] = "red"
    else:
        # Use EX stage as main active if instruction is executing
        if pipe.id_ex["op"] != "NOP":
            stage_colors["EX"] = "red"
        elif pipe.if_id["instr"] != "NOP" and pipe.if_id["instr"] != "END":
            stage_colors["IF"] = "red"

    # ---------- Nodes ----------
    # Instruction Fetch
    dot.node("PC", "PC")
    dot.node("IF_stage", "IF\nInstruction Fetch", color=stage_colors["IF"], style="filled", fillcolor="#fee")
    dot.node("IM", "Instruction Memory", color=stage_colors["IF"])
    
    # Instruction Decode / Register Fetch
    dot.node("ID_stage", "ID\nInstruction Decode/Register Read", color=stage_colors["ID"], style="filled", fillcolor="#fee")
    dot.node("RF", "Register File", color=stage_colors["ID"])
    
    # Execute / ALU
    dot.node("EX_stage", "EX\nALU/Address Calc", color=stage_colors["EX"], style="filled", fillcolor="#fee")
    dot.node("ALU", "ALU", color=stage_colors["EX"])
    
    # Memory
    dot.node("MEM_stage", "MEM\nData Memory Access", color=stage_colors["MEM"], style="filled", fillcolor="#fee")
    dot.node("DM", "Data Memory", color=stage_colors["MEM"])
    
    # Write Back
    dot.node("WB_stage", "WB\nRegister Write Back", color=stage_colors["WB"], style="filled", fillcolor="#fee")
    
    # ---------- Edges ----------
    dot.edge("PC", "IF_stage")
    dot.edge("IF_stage", "IM")
    dot.edge("IM", "ID_stage")
    dot.edge("ID_stage", "RF")
    dot.edge("RF", "EX_stage")
    dot.edge("EX_stage", "ALU")
    dot.edge("ALU", "MEM_stage")
    dot.edge("MEM_stage", "DM")
    dot.edge("DM", "WB_stage")
    
    # Forwarding paths (optional)
    if pipe.forwarding:
        dot.edge("WB_stage", "EX_stage", style="dashed", label="Forwarding")

    return dot


# ----------------- CPU PIPELINE -----------------
class MIPSPipeline:
    def __init__(self):
        self.registers = init_registers()
        self.memory = [0] * 256
        self.mem_activity = {}
        self.pc = 0
        self.cycle = 0
        self.stalls = 0
        self.executed_instrs = 0

        self.if_id = {"instr": "NOP"}
        self.id_ex = {"op": "NOP"}
        self.ex_mem = {"op": "NOP", "result": 0, "rd": None, "mem_addr": None, "store_val": None}
        self.mem_wb = {"data": 0, "rd": None}

        self.hazard_detected = False
        self.hazard_type = None
        self.hazard_explanation = ""
        self.forwarding = True
        self.timeline = []

        # Control Signals
        self.controls = {
            "RegWrite": 0, "MemRead": 0, "MemWrite": 0, "ALUSrc": 0, "Branch": 0
        }

    # ---------- Instruction Parser ----------
    def parse_instruction(self, instr):
        try:
            parts = instr.replace(",", "").split()
            if not parts:
                return {"op": "NOP"}

            op = parts[0].upper()

            if op in ["ADD", "SUB", "MUL"]:
                return {"op": op, "rd": parts[1], "rs": parts[2], "rt": parts[3]}
            if op in ["ADDI", "ORI"]:
                return {"op": op, "rd": parts[1], "rs": parts[2], "imm": int(parts[3])}
            if op == "LUI":
                return {"op": "LUI", "rd": parts[1], "imm": int(parts[2])}
            if op == "LI":
                return {"op": "LI", "rd": parts[1], "imm": int(parts[2])}
            if op in ["LW", "SW", "LB", "LH"]:
                offset, rs = parts[2].split("(")
                rs = rs.replace(")", "")
                return {"op": op, "rt": parts[1], "rs": rs, "imm": int(offset)}
            if op == "BEQ":
                return {"op": "BEQ", "rs": parts[1], "rt": parts[2], "imm": int(parts[3])}
        except Exception as e:
            return {"op": "ERROR", "msg": str(e), "raw": instr}

        return {"op": "NOP"}

    # ---------- Pipeline Step ----------
    def step(self, instructions):
        self.cycle += 1
        self.hazard_detected = False
        self.hazard_type = None
        self.hazard_explanation = ""
        self.controls = {"RegWrite": 0, "MemRead": 0, "MemWrite": 0, "ALUSrc": 0, "Branch": 0}

        # ---- WB ----
        if self.mem_wb["rd"] and self.mem_wb["rd"] != "$zero":
            self.registers[self.mem_wb["rd"]] = self.mem_wb["data"]
            self.controls["RegWrite"] = 1
            self.executed_instrs += 1

        # ---- MEM ----
        mem_data = self.ex_mem["result"]
        if self.ex_mem["mem_addr"] is not None:
            addr = self.ex_mem["mem_addr"] % len(self.memory)
            if self.ex_mem["op"] == "LW":
                mem_data = self.memory[addr]
                self.mem_activity[addr] = "Loaded (LW)"
                self.controls["MemRead"] = 1
            elif self.ex_mem["op"] == "LB":
                mem_data = self.memory[addr] & 0xFF
                self.mem_activity[addr] = "Loaded Byte (LB)"
                self.controls["MemRead"] = 1
            elif self.ex_mem["op"] == "LH":
                mem_data = self.memory[addr] & 0xFFFF
                self.mem_activity[addr] = "Loaded Half (LH)"
                self.controls["MemRead"] = 1
            elif self.ex_mem["op"] == "SW":
                self.memory[addr] = self.ex_mem["store_val"]
                self.mem_activity[addr] = "Stored (SW)"
                self.controls["MemWrite"] = 1

        self.mem_wb = {"data": mem_data, "rd": self.ex_mem["rd"]}

        # ---- EX ----
        ex = self.id_ex
        result, rd, mem_addr, store_val = 0, None, None, None

        if ex["op"] == "ERROR":
            self.hazard_detected = True
            self.hazard_type = "Instruction Error"
            self.hazard_explanation = f"Invalid instruction: {ex['raw']}"
            self.id_ex = {"op": "NOP"}
        else:
            if ex["op"] == "ADD":
                result = self.registers[ex["rs"]] + self.registers[ex["rt"]]
                rd = ex["rd"]
            elif ex["op"] == "SUB":
                result = self.registers[ex["rs"]] - self.registers[ex["rt"]]
                rd = ex["rd"]
            elif ex["op"] == "MUL":
                result = self.registers[ex["rs"]] * self.registers[ex["rt"]]
                rd = ex["rd"]
            elif ex["op"] == "ADDI":
                result = self.registers[ex["rs"]] + ex["imm"]
                rd = ex["rd"]
                self.controls["ALUSrc"] = 1
            elif ex["op"] == "ORI":
                result = self.registers[ex["rs"]] | ex["imm"]
                rd = ex["rd"]
                self.controls["ALUSrc"] = 1
            elif ex["op"] == "LUI":
                result = ex["imm"] << 16
                rd = ex["rd"]
                self.controls["ALUSrc"] = 1
            elif ex["op"] == "LI":
                result = ex["imm"]
                rd = ex["rd"]
                self.controls["ALUSrc"] = 1
            elif ex["op"] in ["LW", "LB", "LH"]:
                mem_addr = self.registers[ex["rs"]] + ex["imm"]
                rd = ex["rt"]
                self.controls["ALUSrc"] = 1
                self.controls["MemRead"] = 1
            elif ex["op"] == "SW":
                mem_addr = self.registers[ex["rs"]] + ex["imm"]
                store_val = self.registers[ex["rt"]]
                self.controls["ALUSrc"] = 1
                self.controls["MemWrite"] = 1
            elif ex["op"] == "BEQ":
                self.controls["Branch"] = 1
                if self.registers[ex["rs"]] == self.registers[ex["rt"]]:
                    self.pc += ex["imm"] * 4

        self.ex_mem = {"op": ex["op"], "result": result, "rd": rd,
                       "mem_addr": mem_addr, "store_val": store_val}

        # ---- ID + Hazard Detection ----
        if self.pc // 4 < len(instructions):
            decoded = self.parse_instruction(instructions[self.pc // 4])
            src = [decoded.get("rs"), decoded.get("rt")]

            # Load-Use hazard
            if self.ex_mem["op"] in ["LW", "LB", "LH"] and self.ex_mem["rd"] in src:
                self.hazard_detected = True
                self.hazard_type = "Load-Use Hazard"
                self.hazard_explanation = "Next instruction needs data from a load instruction."
                self.id_ex = {"op": "NOP"}
                self.stalls += 1
                return

            # RAW hazard
            if self.ex_mem["rd"] and self.ex_mem["rd"] in src:
                if not self.forwarding:
                    self.hazard_detected = True
                    self.hazard_type = "RAW Data Hazard"
                    self.hazard_explanation = "Register value not written back yet."
                    self.id_ex = {"op": "NOP"}
                    self.stalls += 1
                    return

            self.id_ex = decoded

        # ---- IF ----
        if self.pc // 4 < len(instructions):
            self.if_id = {"instr": instructions[self.pc // 4]}
            self.pc += 4
        else:
            self.if_id = {"instr": "END"}

        self.timeline.append({
            "Cycle": self.cycle,
            "IF": self.if_id["instr"],
            "ID": self.id_ex["op"],
            "EX": self.ex_mem["op"],
            "MEM": self.mem_wb["rd"],
            "WB": self.mem_wb["rd"]
        })

    # ---------- CPI ----------
    def get_cpi(self):
        if self.executed_instrs == 0:
            return 0
        return self.cycle / self.executed_instrs


# ----------------- GRAPH -----------------
def draw_pipeline(pipe):
    dot = graphviz.Digraph()
    dot.attr(rankdir="LR")
    dot.node("IF", f"IF\n{pipe.if_id['instr']}")
    dot.node("ID", f"ID\n{pipe.id_ex['op']}")
    dot.node("EX", f"EX\n{pipe.ex_mem['op']}")
    dot.node("MEM", "MEM")
    dot.node("WB", f"WB\n{pipe.mem_wb['rd']}")
    color = "red" if pipe.hazard_detected else "black"
    dot.edge("IF", "ID", color=color)
    dot.edge("ID", "EX")
    dot.edge("EX", "MEM")
    dot.edge("MEM", "WB")
    if pipe.forwarding:
        dot.edge("WB", "EX", style="dashed", label="Forwarding")
    return dot


# ----------------- SIDEBAR -----------------
st.sidebar.title("📘 MIPS Pipeline + Datapath Simulator")
st.sidebar.markdown("""
### 🔹 Control Signals
Shows signals for current EX stage:
- RegWrite, MemRead, MemWrite, ALUSrc, Branch

### 🔹 Forwarding
Avoid stalls by sending results to EX stage.

### 🔹 CPI & Stalls
Compute cycles per instruction dynamically.

### 🔹 Instruction Errors
Invalid instructions highlighted in red.
""")

# ----------------- UI -----------------
st.set_page_config(layout="wide", page_title="Advanced MIPS Simulator")
st.title("🧠 Advanced MIPS Pipeline Simulator")

if "sim" not in st.session_state:
    st.session_state.sim = MIPSPipeline()
    st.session_state.code = """LI $t0, 10
LI $t1, 20
MUL $s0, $t0, $t1
SW $s0, 0($t0)
LW $s1, 0($t0)
"""

sim = st.session_state.sim

col1, col2 = st.columns([1,2])

with col1:
    st.header("Assembly Code")
    code = st.text_area("Enter MIPS Code", st.session_state.code, height=220)
    st.session_state.code = code
    instructions = [i.strip() for i in code.split("\n") if i.strip()]

    sim.forwarding = st.checkbox("Enable Forwarding", True)

    if st.button("▶ Next Cycle"):
        sim.step(instructions)

    if st.button("⏩ Run Program"):
        while sim.pc // 4 < len(instructions):
            sim.step(instructions)

    if st.button("🔄 Reset"):
        st.session_state.sim = MIPSPipeline()
        st.rerun()

    st.subheader("Registers")
    st.table({k:v for k,v in sim.registers.items() if v != 0})

    # st.subheader("Memory Activity (first 16 addresses)")
    # mem_table = {}
    # for i in range(16):
    #     mem_table[i] = f"{sim.memory[i]} ({sim.mem_activity.get(i,'Unused')})"
    # st.table(mem_table)

    st.subheader("Control Signals (EX Stage)")
    st.table(sim.controls)

    st.subheader("Performance")
    st.info(f"Cycles = {sim.cycle} | Stalls = {sim.stalls} | CPI = {sim.get_cpi():.2f}")

with col2:
    st.header("Pipeline View")
    if sim.hazard_detected:
        st.error(f"⚠️ {sim.hazard_type}")
        st.warning(sim.hazard_explanation)
    st.graphviz_chart(draw_pipeline(sim))
    st.subheader("Pipeline Timing Table")
    if sim.timeline:
        st.table(sim.timeline)
    st.subheader("Status")
    st.info(f"PC = {sim.pc} | Cycle = {sim.cycle}")
    # with st.expander("Pipeline View"):
    #     st.graphviz_chart(draw_pipeline(sim))
    # with st.expander("Datapath View"):
    #     st.graphviz_chart(draw_datapath(sim))


# ----------------- STATIC FOOTER -----------------
st.markdown("""
<style>
.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: #0e1117;
color: white;
text-align: center;
padding: 8px;
font-size: 14px;
}
</style>

<div class="footer">
Developed by <b>Muhammad Khubaib Ahmad</b> — MIPS Pipeline Educational Simulator
</div>
""", unsafe_allow_html=True)