# translations.py
"""
Dictionnaire de traductions — Him Structural
Langues : fr (Français), en (English), zh (中文)
"""

TRANSLATIONS = {
    # ══════════════════════════════════════════════
    # FENÊTRE PRINCIPALE
    # ══════════════════════════════════════════════
    "app_title": {
        "fr": "Him Structural — Analyse de structures",
        "en": "Him Structural — Structural Analysis",
        "zh": "Him Structural — 结构分析",
    },

    # ══════════════════════════════════════════════
    # MENUS
    # ══════════════════════════════════════════════
    "menu_file":          {"fr": "Fichier",    "en": "File",     "zh": "文件"},
    "menu_file_save":     {"fr": "Enregistrer","en": "Save",     "zh": "保存"},
    "menu_file_open":     {"fr": "Ouvrir",     "en": "Open",     "zh": "打开"},
    "menu_file_exit":     {"fr": "Quitter",    "en": "Exit",     "zh": "退出"},
    "menu_settings":      {"fr": "Paramètres", "en": "Settings", "zh": "设置"},

    "menu_edit":          {"fr": "Édition",    "en": "Edit",     "zh": "编辑"},
    "menu_edit_undo":     {"fr": "Annuler",    "en": "Undo",     "zh": "撤销"},
    "menu_edit_redo":     {"fr": "Rétablir",   "en": "Redo",     "zh": "重做"},
    "menu_edit_delete":   {"fr": "Supprimer sélection", "en": "Delete selection", "zh": "删除选择"},

    "menu_view":              {"fr": "Vue",                    "en": "View",          "zh": "视图"},
    "menu_view_section":      {"fr": "Section",                "en": "Section",       "zh": "截面"},
    "menu_view_2d":           {"fr": "2D",                     "en": "2D",            "zh": "2D"},
    "menu_view_snap":         {"fr": "Magnétisme grille",      "en": "Grid snap",     "zh": "网格吸附"},
    "menu_view_grid":         {"fr": "Afficher la grille",     "en": "Show grid",     "zh": "显示网格"},

    "menu_diagrams":          {"fr": "Diagrammes",             "en": "Diagrams",      "zh": "图表"},
    "menu_diagrams_config":   {"fr": "Configuration…",        "en": "Configuration…","zh": "配置…"},
    "menu_diagrams_combo":    {"fr": "Choisir combinaison",    "en": "Pick combination","zh": "选择组合"},
    "menu_diagrams_show_bmd": {"fr": "Afficher/Masquer BMD",  "en": "Toggle BMD",    "zh": "显示/隐藏弯矩图"},
    "menu_diagrams_show_sfd": {"fr": "Afficher/Masquer SFD",  "en": "Toggle SFD",    "zh": "显示/隐藏剪力图"},
    "menu_diagrams_auto_scale":   {"fr": "Échelle automatique",  "en": "Auto scale",    "zh": "自动比例"},
    "menu_diagrams_manual_scale": {"fr": "Échelle manuelle…",   "en": "Manual scale…", "zh": "手动比例…"},
    "menu_diagrams_envelope":     {
        "fr": "Enveloppe (pire combinaison)",
        "en": "Envelope (worst combo)",
        "zh": "包络（最差组合）",
    },
    "menu_diagrams_no_analysis": {
        "fr": "Aucune analyse effectuée",
        "en": "No analysis performed",
        "zh": "未进行分析",
    },

    "menu_calc":          {"fr": "Calculs",          "en": "Calculations",  "zh": "计算"},
    "menu_calc_combos":   {"fr": "Load Combinations","en": "Load Combinations","zh": "荷载组合"},
    "menu_calc_rebars":   {"fr": "Ferraillage",      "en": "Rebars",        "zh": "钢筋计算"},
    "menu_calc_run":      {"fr": "Lancer l'analyse", "en": "Run Analysis",  "zh": "运行分析"},

    "menu_him_ai":        {"fr": "Him IA",                  "en": "Him AI",                "zh": "Him 智能"},
    "menu_him_ai_open":   {"fr": "Ouvrir Him IA Assistant", "en": "Open Him AI Assistant", "zh": "打开 Him 智能助手"},
    "menu_help":          {"fr": "Aide",   "en": "Help",  "zh": "帮助"},

    # ══════════════════════════════════════════════
    # TOOLBAR
    # ══════════════════════════════════════════════
    "tool_select":     {"fr": "Sélection", "en": "Select", "zh": "选择"},
    "tool_select_tip": {"fr": "Outil de sélection (S)", "en": "Selection tool (S)", "zh": "选择工具 (S)"},
    "tool_node":       {"fr": "Nœud",     "en": "Node",   "zh": "节点"},
    "tool_node_tip":   {"fr": "Créer un nœud (N)",      "en": "Create node (N)",   "zh": "创建节点 (N)"},
    "tool_beam":       {"fr": "Poutre",   "en": "Beam",   "zh": "梁"},
    "tool_beam_tip":   {"fr": "Créer une poutre (B)",   "en": "Create beam (B)",   "zh": "创建梁 (B)"},
    "tool_load":       {"fr": "Charge",   "en": "Load",   "zh": "荷载"},
    "tool_load_tip":   {"fr": "Ajouter une charge (L)", "en": "Add load (L)",      "zh": "添加荷载 (L)"},

    # ══════════════════════════════════════════════
    # BARRE DE STATUT
    # ══════════════════════════════════════════════
    "status_ready": {
        "fr": "✅ Him Structural prêt. Créez des nœuds et des poutres pour commencer.",
        "en": "✅ Him Structural ready. Create nodes and beams to get started.",
        "zh": "✅ Him Structural 就绪。创建节点和梁以开始使用。",
    },
    "status_mode":             {"fr": "Mode : {}",          "en": "Mode: {}",           "zh": "模式：{}"},
    "status_section_active":   {"fr": "Section active : {}", "en": "Active section: {}", "zh": "当前截面：{}"},
    "status_no_section":       {"fr": "Aucune section sélectionnée", "en": "No section selected", "zh": "未选择截面"},
    "status_saved":            {"fr": "✅ Projet enregistré : {}",  "en": "✅ Project saved: {}", "zh": "✅ 项目已保存：{}"},
    "status_save_error":       {"fr": "❌ Erreur lors de la sauvegarde", "en": "❌ Save error", "zh": "❌ 保存错误"},
    "status_loaded":           {"fr": "✅ Projet chargé : {}",      "en": "✅ Project loaded: {}", "zh": "✅ 项目已加载：{}"},
    "status_load_error":       {"fr": "❌ Erreur lors du chargement", "en": "❌ Load error", "zh": "❌ 加载错误"},
    "status_settings_applied": {"fr": "✅ Paramètres appliqués",    "en": "✅ Settings applied", "zh": "✅ 设置已应用"},
    "status_analysis_ok": {
        "fr": "✅ Analyse terminée - {} poutre(s) calculée(s)",
        "en": "✅ Analysis complete - {} beam(s) calculated",
        "zh": "✅ 分析完成 - 已计算 {} 根梁",
    },
    "status_analysis_error":   {"fr": "❌ L'analyse a échoué", "en": "❌ Analysis failed", "zh": "❌ 分析失败"},
    "status_combo_shown": {
        "fr": "✅ Combinaison affichée : {}",
        "en": "✅ Combination shown: {}",
        "zh": "✅ 已显示组合：{}",
    },
    "status_auto_scale": {
        "fr": "✅ Échelle automatique activée",
        "en": "✅ Auto scale enabled",
        "zh": "✅ 自动比例已启用",
    },

    # ══════════════════════════════════════════════
    # MODES
    # ══════════════════════════════════════════════
    "mode_select": {"fr": "Sélection",    "en": "Selection",    "zh": "选择"},
    "mode_node":   {"fr": "Créer nœud",   "en": "Create node",  "zh": "创建节点"},
    "mode_beam":   {"fr": "Créer poutre", "en": "Create beam",  "zh": "创建梁"},

    # ══════════════════════════════════════════════
    # DOCK WIDGETS
    # ══════════════════════════════════════════════
    "dock_properties": {"fr": "Propriétés",       "en": "Properties",      "zh": "属性"},
    "dock_sections":   {"fr": "Sections & Charges","en": "Sections & Loads","zh": "截面与荷载"},

    # ══════════════════════════════════════════════
    # PANNEAU PROPRIÉTÉS
    # ══════════════════════════════════════════════
    "prop_title":         {"fr": "Informations élément", "en": "Element info",   "zh": "元素信息"},
    "prop_type":          {"fr": "Type :",              "en": "Type:",           "zh": "类型："},
    "prop_id":            {"fr": "ID :",                "en": "ID:",             "zh": "标识："},
    "prop_x":             {"fr": "X :",                 "en": "X:",              "zh": "X："},
    "prop_y":             {"fr": "Y :",                 "en": "Y:",              "zh": "Y："},
    "prop_length":        {"fr": "Longueur :",          "en": "Length:",         "zh": "长度："},
    "prop_none":          {"fr": "Aucun",               "en": "None",            "zh": "无"},

    "prop_supports":      {"fr": "Conditions d'appui",  "en": "Support conditions", "zh": "支座条件"},
    "prop_support_type":  {"fr": "Type d'appui :",      "en": "Support type:",      "zh": "支座类型："},
    "support_free":       {"fr": "⚪ Libre",             "en": "⚪ Free",             "zh": "⚪ 自由端"},
    "support_pin":        {"fr": "🔵 Articulé (dx=dy=0)",       "en": "🔵 Pinned (dx=dy=0)",       "zh": "🔵 铰支座 (dx=dy=0)"},
    "support_roller":     {"fr": "🔄 Appui simple roulant (dy=0)", "en": "🔄 Roller (dy=0)",         "zh": "🔄 滚动支座 (dy=0)"},
    "support_fixed":      {"fr": "⬛ Encastrement (dx=dy=rz=0)", "en": "⬛ Fixed (dx=dy=rz=0)",    "zh": "⬛ 固定端 (dx=dy=rz=0)"},

    "prop_section_mat":   {"fr": "Section & Matériau",  "en": "Section & Material", "zh": "截面与材料"},
    "prop_concrete_grade":{"fr": "Grade béton :",       "en": "Concrete grade:",    "zh": "混凝土强度："},
    "prop_section":       {"fr": "Section :",           "en": "Section:",           "zh": "截面："},
    "prop_no_section":    {"fr": "— aucune —",          "en": "— none —",           "zh": "— 无 —"},
    "prop_loads":         {"fr": "Charges appliquées",  "en": "Applied loads",      "zh": "施加荷载"},
    "prop_no_loads":      {"fr": "Aucune charge",       "en": "No loads",           "zh": "无荷载"},
    "prop_add_load":      {"fr": "➕ Ajouter charge",   "en": "➕ Add load",         "zh": "➕ 添加荷载"},
    "prop_apply":         {"fr": "✅ Appliquer",         "en": "✅ Apply",            "zh": "✅ 应用"},

    # ══════════════════════════════════════════════
    # PARAMÈTRES
    # ══════════════════════════════════════════════
    "settings_title":     {"fr": "Paramètres — Him Structural", "en": "Settings — Him Structural", "zh": "设置 — Him Structural"},
    "settings_tab_units": {"fr": "Unités",     "en": "Units",      "zh": "单位"},
    "settings_tab_convert":  {"fr": "Conversion","en": "Conversion", "zh": "换算"},
    "settings_tab_output":   {"fr": "Sortie",    "en": "Output",     "zh": "输出"},
    "settings_tab_language": {"fr": "Langue",    "en": "Language",   "zh": "语言"},
    "settings_save_btn": {
        "fr": "💾  Sauvegarder et appliquer",
        "en": "💾  Save and apply",
        "zh": "💾  保存并应用",
    },
    "settings_saved_msg": {
        "fr": "✅ Paramètres enregistrés et appliqués en temps réel !\nToutes les longueurs, coordonnées et affichages sont mis à jour.",
        "en": "✅ Settings saved and applied in real time!\nAll lengths, coordinates and displays are updated.",
        "zh": "✅ 设置已实时保存并应用！\n所有长度、坐标和显示均已更新。",
    },
    "settings_success": {"fr": "Succès",  "en": "Success",  "zh": "成功"},

    "settings_unit_system":  {"fr": "Système d'unités :", "en": "Unit system:",    "zh": "单位制："},
    "settings_length_unit":  {"fr": "Unité de longueur :","en": "Length unit:",    "zh": "长度单位："},
    "settings_force_unit":   {"fr": "Unité de force :",   "en": "Force unit:",     "zh": "力的单位："},
    "settings_moment_unit":  {"fr": "Unité de moment :",  "en": "Moment unit:",    "zh": "力矩单位："},
    "settings_moment_fixed": {"fr": "kN·m (fixe)",        "en": "kN·m (fixed)",    "zh": "kN·m（固定）"},
    "settings_section_unit": {"fr": "Sections :",         "en": "Sections:",       "zh": "截面："},
    "settings_section_fixed":{"fr": "mm (toujours)",      "en": "mm (always)",     "zh": "mm（固定）"},

    "settings_display":   {"fr": "Affichage",           "en": "Display",             "zh": "显示"},
    "settings_decimals":  {"fr": "Décimales affichées :","en": "Displayed decimals:", "zh": "显示小数位："},
    "settings_invert_bmd":{
        "fr": "Inverser convention des moments fléchissants",
        "en": "Invert bending moment convention",
        "zh": "翻转弯矩约定",
    },

    "settings_language_title": {
        "fr": "Langue de l'interface",
        "en": "Interface language",
        "zh": "界面语言",
    },
    "settings_language_label": {"fr": "Langue :",  "en": "Language:", "zh": "语言："},
    "settings_language_note": {
        "fr": "Le changement de langue s'applique immédiatement à toute\nl'interface, y compris Him IA.",
        "en": "Language changes apply immediately to the entire\ninterface, including Him AI.",
        "zh": "语言更改将立即应用于整个界面，\n包括 Him 智能助手。",
    },
    "lang_fr": {"fr": "🇫🇷  Français", "en": "🇫🇷  French",  "zh": "🇫🇷  法语"},
    "lang_en": {"fr": "🇬🇧  Anglais",  "en": "🇬🇧  English", "zh": "🇬🇧  英语"},
    "lang_zh": {"fr": "🇨🇳  Chinois",  "en": "🇨🇳  Chinese", "zh": "🇨🇳  中文"},

    # ══════════════════════════════════════════════
    # DIALOGUES GÉNÉRIQUES
    # ══════════════════════════════════════════════
    "dlg_ok":     {"fr": "OK",       "en": "OK",     "zh": "确定"},
    "dlg_cancel": {"fr": "Annuler",  "en": "Cancel", "zh": "取消"},
    "dlg_close":  {"fr": "Fermer",   "en": "Close",  "zh": "关闭"},
    "dlg_yes":    {"fr": "Oui",      "en": "Yes",    "zh": "是"},
    "dlg_no":     {"fr": "Non",      "en": "No",     "zh": "否"},
    "dlg_apply":  {"fr": "Appliquer","en": "Apply",  "zh": "应用"},
    "dlg_save":   {"fr": "Enregistrer","en": "Save", "zh": "保存"},
    "dlg_delete": {"fr": "Supprimer","en": "Delete", "zh": "删除"},

    # ══════════════════════════════════════════════
    # CHARGES
    # ══════════════════════════════════════════════
    "loads_title":       {"fr": "Gestion des charges",  "en": "Load management",   "zh": "荷载管理"},
    "loads_point":       {"fr": "Charge ponctuelle",    "en": "Point load",         "zh": "集中荷载"},
    "loads_distributed": {"fr": "Charge répartie",      "en": "Distributed load",   "zh": "分布荷载"},
    "loads_permanent":   {"fr": "Permanente (G)",        "en": "Permanent (G)",      "zh": "永久荷载 (G)"},
    "loads_variable":    {"fr": "Variable (Q)",          "en": "Variable (Q)",       "zh": "可变荷载 (Q)"},
    "loads_intensity":   {"fr": "Intensité (kN) :",      "en": "Intensity (kN):",    "zh": "强度 (kN)："},
    "loads_position":    {"fr": "Position (m) :",        "en": "Position (m):",      "zh": "位置 (m)："},
    "loads_no_beam": {
        "fr": "Créez d'abord des nœuds et des poutres avant d'ajouter des charges.",
        "en": "Create nodes and beams first before adding loads.",
        "zh": "请先创建节点和梁，再添加荷载。",
    },

    # ══════════════════════════════════════════════
    # COMBINAISONS
    # ══════════════════════════════════════════════
    "combos_title":      {"fr": "Combinaisons de charges", "en": "Load combinations", "zh": "荷载组合"},
    "combos_import":     {"fr": "Importer depuis l'EC2",   "en": "Import from EC2",   "zh": "从 EC2 导入"},
    "combos_delete_all": {"fr": "Supprimer tout",          "en": "Delete all",        "zh": "全部删除"},
    "combos_save":       {"fr": "💾 Sauvegarder",          "en": "💾 Save",           "zh": "💾 保存"},
    "combos_add":        {"fr": "➕ Ajouter",              "en": "➕ Add",            "zh": "➕ 添加"},

    # ══════════════════════════════════════════════
    # FERRAILLAGE
    # ══════════════════════════════════════════════
    "rebar_title":           {"fr": "Ferraillage — Poutre {}", "en": "Rebar design — Beam {}", "zh": "钢筋设计 — 梁 {}"},
    "rebar_no_beam":         {"fr": "Aucune poutre sélectionnée",   "en": "No beam selected",          "zh": "未选择梁"},
    "rebar_no_beam_msg":     {
        "fr": "Cliquez sur une poutre dans le canvas avant d'ouvrir la vue section.",
        "en": "Click on a beam in the canvas before opening the section view.",
        "zh": "请先在画布中点击一根梁，再打开截面视图。",
    },
    "rebar_no_analysis":     {"fr": "Pas d'analyse",   "en": "No analysis",     "zh": "无分析结果"},
    "rebar_no_analysis_msg": {
        "fr": "Lancez d'abord 'Lancer l'analyse'.",
        "en": "Run 'Run Analysis' first.",
        "zh": "请先运行分析。",
    },
    "rebar_zero_moment":     {"fr": "Moment nul",      "en": "Zero moment",     "zh": "弯矩为零"},
    "rebar_zero_moment_msg": {
        "fr": "Mmax = {:.3f} kN·m — aucun ferraillage nécessaire.",
        "en": "Mmax = {:.3f} kN·m — no reinforcement needed.",
        "zh": "Mmax = {:.3f} kN·m — 无需配筋。",
    },
    "rebar_not_rect": {
        "fr": "Section non rectangulaire",
        "en": "Non-rectangular section",
        "zh": "非矩形截面",
    },
    "rebar_not_rect_msg": {
        "fr": "Cette fonctionnalité est réservée aux sections rectangulaires.",
        "en": "This feature is only for rectangular sections.",
        "zh": "此功能仅适用于矩形截面。",
    },
    "rebar_close": {"fr": "Fermer", "en": "Close", "zh": "关闭"},

    # ══════════════════════════════════════════════
    # HIM AI
    # ══════════════════════════════════════════════
    "ai_title":       {"fr": "Him IA",    "en": "Him AI",   "zh": "Him 智能"},
    "ai_send":        {"fr": "Envoyer",   "en": "Send",     "zh": "发送"},
    "ai_clear":       {"fr": "Effacer",   "en": "Clear",    "zh": "清除"},
    "ai_placeholder": {
        "fr": "Posez une question ou donnez un ordre…",
        "en": "Ask a question or give a command…",
        "zh": "提问或输入指令…",
    },
    "ai_welcome": {
        "fr": "👋 Bonjour ! Je suis <b>Him IA</b>. Je peux créer des nœuds, poutres, sections, lancer l'analyse, calculer le ferraillage…",
        "en": "👋 Hello! I am <b>Him AI</b>. I can create nodes, beams, sections, run analysis, calculate rebar…",
        "zh": "👋 您好！我是 <b>Him 智能助手</b>。我可以创建节点、梁、截面，运行分析，计算钢筋配置…",
    },
    "ai_cleared": {
        "fr": "💬 Conversation effacée.",
        "en": "💬 Conversation cleared.",
        "zh": "💬 对话已清除。",
    },
    "ai_no_token": {
        "fr": "GITHUB_TOKEN manquant.\nCrée un token sur https://github.com/settings/tokens (scope 'models:read') et relance l'app.",
        "en": "GITHUB_TOKEN missing.\nCreate a token at https://github.com/settings/tokens (scope 'models:read') and restart the app.",
        "zh": "缺少 GITHUB_TOKEN。\n请在 https://github.com/settings/tokens 创建令牌（权限 'models:read'）并重启应用。",
    },
    "ai_lang_instruction": {
        "fr": "IMPORTANT : Tu DOIS répondre UNIQUEMENT en français, quelle que soit la langue de l'utilisateur.",
        "en": "IMPORTANT: You MUST respond ONLY in English, regardless of the user's language.",
        "zh": "重要提示：无论用户使用何种语言，你必须只用中文回复。",
    },

    # ══════════════════════════════════════════════
    # SECTIONS PANEL
    # ══════════════════════════════════════════════
    "sections_title":      {"fr": "Bibliothèque de sections", "en": "Section library",   "zh": "截面库"},
    "sections_add":        {"fr": "➕ Nouvelle section",       "en": "➕ New section",     "zh": "➕ 新截面"},
    "sections_edit":       {"fr": "✏️ Modifier",              "en": "✏️ Edit",           "zh": "✏️ 编辑"},
    "sections_delete":     {"fr": "🗑 Supprimer",             "en": "🗑 Delete",         "zh": "🗑 删除"},
    "sections_no_preview": {"fr": "Aucune section sélectionnée", "en": "No section selected", "zh": "未选择截面"},

    # ══════════════════════════════════════════════
    # DIAGRAMMES
    # ══════════════════════════════════════════════
    "diag_title":       {"fr": "Configuration des diagrammes", "en": "Diagram settings",  "zh": "图表设置"},
    "diag_bmd":         {"fr": "Diagramme des moments (BMD)",  "en": "Bending moment (BMD)", "zh": "弯矩图 (BMD)"},
    "diag_sfd":         {"fr": "Diagramme des efforts tranchants (SFD)", "en": "Shear force (SFD)", "zh": "剪力图 (SFD)"},
    "diag_show":        {"fr": "Afficher",          "en": "Show",       "zh": "显示"},
    "diag_color":       {"fr": "Couleur",           "en": "Color",      "zh": "颜色"},
    "diag_fill":        {"fr": "Remplissage",       "en": "Fill",       "zh": "填充"},
    "diag_line_width":  {"fr": "Épaisseur de trait","en": "Line width", "zh": "线宽"},
    "diag_scale_auto":  {"fr": "Automatique",       "en": "Automatic",  "zh": "自动"},
    "diag_scale_manual":{"fr": "Manuelle",          "en": "Manual",     "zh": "手动"},
    "diag_save_apply":  {
        "fr": "💾 Sauvegarder et appliquer",
        "en": "💾 Save and apply",
        "zh": "💾 保存并应用",
    },

    # ══════════════════════════════════════════════
    # MESSAGES DIVERS
    # ══════════════════════════════════════════════
    "analysis_model_invalid": {"fr": "Modèle incomplet", "en": "Incomplete model", "zh": "模型不完整"},
    "confirm_delete_title":   {"fr": "Confirmer la suppression", "en": "Confirm deletion", "zh": "确认删除"},
    "confirm_delete_msg":     {"fr": "Supprimer l'élément sélectionné ?", "en": "Delete selected element?", "zh": "确定要删除所选元素吗？"},
    "error_title":            {"fr": "Erreur",       "en": "Error",       "zh": "错误"},
    "info_title":             {"fr": "Information",  "en": "Information", "zh": "信息"},
    "warning_title":          {"fr": "Avertissement","en": "Warning",     "zh": "警告"},
}