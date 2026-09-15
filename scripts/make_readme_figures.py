import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
plt.rcParams["font.family"]="DejaVu Sans"
M="rlflow-parkour/docs/media/"; C="#187C8C"
H=json.load(open("showcase/histories.json"))
passes=[("c1b",.35,.89),("c3",.45,.95),("c3'",.50,.97),("c6",.55,.95),("c8",.60,.80),("c10",.62,.95),("c12",.65,.95),("c19",.68,.89),("c20",.71,.81),("c23",.73,.81),
        ("c25",.75,.94),("c26",.77,.94),("c27",.79,.92),("c30",.80,.94),("c31",.81,.75),("c35",.82,.86),("c38",.83,.91),("c40",.86,.875),
        ("c43",.872,.81),("c44",.884,.92),("c45",.896,.92),("c49",.908,.89),("c51",.92,.75)]
# 0. curriculum
fig,ax=plt.subplots(figsize=(9,4.3),dpi=150); x=list(range(len(passes)))
ax.plot(x,[p[1]*100 for p in passes],color=C,lw=2.2,marker="o",ms=5,label="Map difficulty of each passed stage (%)",zorder=3)
ax2=ax.twinx(); ax2.bar(x,[p[2]*100 for p in passes],width=.55,color=C,alpha=.18,label="Frozen-eval completion (%)"); ax2.set_ylim(0,100); ax2.set_ylabel("Completion (%, 64 episodes)")
for i,p in enumerate(passes):
    if i%3==0 or i==len(passes)-1: ax.annotate(p[0],(i,p[1]*100),textcoords="offset points",xytext=(0,7),ha="center",fontsize=7,color="#444")
ax.axvspan(17.5,len(passes)-.5,color="#f2b134",alpha=.12)
ax.text(20.2,37,"Probe-guided per-axis curriculum",ha="center",fontsize=8,color="#8a5a00"); ax.text(8,37,"Uniform-difficulty curriculum (+0.02–0.05 per stage)",ha="center",fontsize=8,color="#0e4d57")
ax.set_ylim(30,100); ax.set_xlabel("Curriculum stage (in order of passing)"); ax.set_ylabel("Map difficulty (%)"); ax.set_xticks(x); ax.set_xticklabels([p[0] for p in passes],rotation=60,fontsize=7)
ax.set_title("24-gap course difficulty 25% → 92%: map difficulty and completion of the 23 passed stages",fontsize=10.5); ax.grid(alpha=.25)
h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels(); ax.legend(h1+h2,l1+l2,loc="upper left",fontsize=8)
plt.tight_layout(); plt.savefig(M+"curriculum.png"); plt.close()
# 1. training curves
fig,ax=plt.subplots(figsize=(9,4.2),dpi=150)
sel=[("c1b .35","map 35%"),("c3 .45","45%"),("c20 .71","71%"),("c27 .79","79%"),("c38 .83","83%"),("c40 .86","86%"),("c45","per-axis (c45)"),("c49","per-axis (c49)"),("c51","per-axis (c51)")]
cm=plt.cm.viridis(np.linspace(0,.95,len(sel)))
for (k,lab),col in zip(sel,cm):
    h=H[k]["ema"]; ax.plot([s/1e6 for s,_ in h],[v for _,v in h],color=col,lw=1.8,label=lab)
ax.set_xlabel("Environment steps (M)"); ax.set_ylabel("Training completion EMA (with exploration noise)"); ax.set_ylim(0,1); ax.grid(alpha=.25)
ax.set_title("Learning curves of the best trial per stage — same budget (2048 envs × 1200 iters) at every difficulty",fontsize=10)
ax.legend(fontsize=8,ncol=3,loc="lower right"); plt.tight_layout(); plt.savefig(M+"training-curves.png"); plt.close()
# 2. stage outcomes
P=[(p[1],p[2]) for p in passes]
partial=[(.65,.53),(.68,.39),(.68,.42),(.68,.625),(.68,.73),(.68,.66),(.73,.53),(.75,.53),(.80,.64),(.82,.5),(.896,.5625),(.92,.5156),(.92,.72),(.956,.156)]
collapse=[(.74,0),(.81,.03),(.83,.05),(.89,0)]
fig,ax=plt.subplots(figsize=(9,4.2),dpi=150)
ax.axhline(75,color="#999",ls="--",lw=1); ax.text(27,77,"pass threshold 75%",fontsize=8,color="#666")
ax.scatter([p[0]*100 for p in P],[p[1]*100 for p in P],s=46,color=C,label="Passed → parent of the next stage",zorder=3)
ax.scatter([p[0]*100 for p in partial],[p[1]*100 for p in partial],s=40,facecolors="none",edgecolors="#e0a100",lw=1.6,label="Below threshold → continued on the same map",zorder=3)
ax.scatter([p[0]*100 for p in collapse],[p[1]*100 for p in collapse],s=60,marker="x",color="#c0392b",lw=2,label="Collapse → back one stage (cause: fork learning rate)",zorder=3)
ax.set_xlabel("Map difficulty (%, mean of 5 axes)"); ax.set_ylabel("Frozen-eval completion (%)"); ax.set_xlim(25,100); ax.set_ylim(-3,103); ax.grid(alpha=.25)
ax.set_title("Stage outcomes: passed, below threshold, collapsed",fontsize=11); ax.legend(fontsize=8,loc="lower left")
plt.tight_layout(); plt.savefig(M+"stage-outcomes.png"); plt.close()
# 3. probe matrix
axes=["gap","turn","tilt","height","size"]; levels=[".89",".92",".93",".95","1.0"]
vals={"gap":[47,3,0,None,0],"turn":[43,0,None,None,0],"tilt":[41,0,None,None,0],"height":[58,31,18,None,0],"size":[52,30,None,None,0]}
fig,ax=plt.subplots(figsize=(7,3.4),dpi=150)
grid=np.array([[np.nan if v is None else v for v in vals[a]] for a in axes],dtype=float)
im=ax.imshow(grid,cmap="YlGnBu",vmin=0,vmax=64,aspect="auto")
for i,a in enumerate(axes):
    for j,v in enumerate(vals[a]):
        ax.text(j,i,"—" if v is None else f"{v}/64",ha="center",va="center",fontsize=9,color="white" if (v or 0)>34 else "#222")
ax.set_xticks(range(len(levels))); ax.set_xticklabels([f"axis at {l}" for l in levels]); ax.set_yticks(range(len(axes))); ax.set_yticklabels(["gap length","turn angle","pad tilt","height change","pad size"])
ax.set_title("Frozen probes of the 86% policy: completions when one axis is raised (others at .86)",fontsize=9.5); plt.colorbar(im,ax=ax,fraction=.04,label="completions / 64")
plt.tight_layout(); plt.savefig(M+"probe-matrix.png"); plt.close()
# 4. per-axis frontier
stages=["c40","c43","c44","c45","c49","c51"]
fr={"gap":[.86,.89,.89,.89,.89,.89],"turn":[.86,.89,.89,.89,.92,.92],"tilt":[.86,.86,.86,.86,.86,.86],"height":[.86,.86,.89,.92,.92,.95],"size":[.86,.86,.89,.92,.95,.98]}
fig,ax=plt.subplots(figsize=(8,3.8),dpi=150)
for (a,lab),mk in zip([("gap","gap length"),("turn","turn angle"),("tilt","pad tilt"),("height","height change"),("size","pad size")],"osD^v"):
    ax.plot(stages,[v*100 for v in fr[a]],marker=mk,lw=1.8,label=lab)
ax.set_ylim(84,100); ax.set_ylabel("Axis difficulty (%)"); ax.grid(alpha=.25); ax.legend(fontsize=8,ncol=5,loc="upper left")
ax.set_title("Per-axis frontier under the per-axis curriculum — height and size move fast, tilt and gap length slowly",fontsize=9.5)
plt.tight_layout(); plt.savefig(M+"axis-frontier.png"); plt.close()
# 5. std sweep
fig,ax=plt.subplots(figsize=(7,3.6),dpi=150)
for k,lab,col in [("c40 .86","min_std 0.04",C),("c40 std.06","min_std 0.06","#e0a100"),("c40 std.08","min_std 0.08","#c0392b")]:
    h=H[k]["ema"]; ax.plot([s/1e6 for s,_ in h],[v for _,v in h],lw=1.8,color=col,label=lab)
ax.set_xlabel("Environment steps (M)"); ax.set_ylabel("Training completion EMA"); ax.set_ylim(0,1); ax.grid(alpha=.25); ax.legend(fontsize=8)
ax.set_title("86% map, sweep over the exploration-noise floor (same parent and LR) — lower noise wins",fontsize=9.5)
plt.tight_layout(); plt.savefig(M+"std-sweep.png"); plt.close()
# 6. fork LR
fig,ax=plt.subplots(figsize=(7,3.6),dpi=150)
for fn,lab,col in [("showcase/forklr-2e-4.jsonl","fork LR 2e-4 (restart at config value)","#c0392b"),("showcase/forklr-1.5e-5.jsonl","fork LR 1.5e-5 (inherited from parent)",C)]:
    rows=[json.loads(l) for l in open(fn)]
    ax.plot([r["iteration"] for r in rows],[r.get("terminal_mean_surface_transfers") or 0 for r in rows],lw=1.8,color=col,label=lab)
ax.set_xlabel("PPO iteration"); ax.set_ylabel("Mean transfers at episode end (24 = full course)"); ax.grid(alpha=.25); ax.legend(fontsize=8)
ax.set_title("Same 86% policy forked onto the 0.89 map — a learning-rate restart destroys the policy",fontsize=9.5)
plt.tight_layout(); plt.savefig(M+"fork-lr.png"); plt.close()
print("figs ok")
