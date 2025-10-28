# LangGraph Kütüphaneleri
from langgraph.graph import StateGraph, END, START
from state import APAState
import pandas as pd
from scapper import WebScraper
from nodes import (
    load_data_node,
    get_labels_node,
    decide_fill_plan_node,
    execute_fill_node,
    is_finished_node
)   
"""RPA iş akışını (graph) oluşturur ve derler."""
workflow = StateGraph(APAState)

# 1. Düğümleri Tanımla
workflow.add_node("load_data", load_data_node)
workflow.add_node("get_labels", get_labels_node)
workflow.add_node("decide_fill_plan", decide_fill_plan_node)
workflow.add_node("execute_fill", execute_fill_node)

# 2. Başlangıç Noktası
workflow.set_entry_point("load_data")

# 3. Kenarları Tanımla

# Veri yüklendikten sonra etiketleri okumaya başla
workflow.add_edge("load_data", "get_labels")

# Etiketler okunduktan sonra LLM Agent'tan planı iste
workflow.add_edge("get_labels", "decide_fill_plan")

# LLM planı yaptıktan sonra doldurma işlemini yap
workflow.add_edge("decide_fill_plan", "execute_fill")

# Doldurma işlemi bittikten sonra döngü bitti mi diye kontrol et
workflow.add_conditional_edges(
    "execute_fill",
    is_finished_node,
    {
        "continue": "get_labels",         # Devam et: Yeni form etiketlerini oku
        "finished": END,                  # Bitti: İş akışını sonlandır
        "end_with_error": END             # Hata: İş akışını sonlandır
    }
)

app = workflow.compile(
    name="APA Challenge Workflow"
)

initial_state = APAState(
    df=pd.DataFrame(), 
    current_row_index=0, 
    max_rows=0, 
    form_labels=[], 
    current_plan={}, 
    error_message=""
)

for state in app.stream(initial_state, {"recursion_limit": 100}):
    print(f"\nGüncel Durum Anahtarları: {list(state.keys())}")

