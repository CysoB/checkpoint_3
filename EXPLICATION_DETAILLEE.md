# 🧠 Explication Détaillée : Comment fonctionne la Memory dans LCEL

## 📋 Table des Matières

1. [Le Problème](#le-problème)
2. [La Solution : RunnableWithMessageHistory](#la-solution)
3. [Ce qui se passe vraiment](#ce-qui-se-passe-vraiment)
4. [Architecture du Flux](#architecture-du-flux)
5. [Points Critiques](#points-critiques)

---

## 🎯 Le Problème

Dans une conversation normale avec un LLM, chaque appel est **indépendant** :

```
Tour 1:
User: "Je m'appelle Samyr"
LLM: "Bonjour Samyr !"

Tour 2:
User: "Quel est mon nom ?"
LLM: "Je ne sais pas, vous ne me l'avez pas dit."
```

Le LLM **oublie** tout entre chaque appel. C'est le problème de la **statelessness**.

---

## ✅ La Solution : RunnableWithMessageHistory

`RunnableWithMessageHistory` est un **wrapper** qui :

1. ✅ Récupère l'historique avant chaque appel
2. ✅ Injecte l'historique dans le prompt
3. ✅ Appelle le pipeline LCEL
4. ✅ Sauvegarde la nouvelle interaction dans l'historique

### Schéma Conceptuel

```
Sans Memory:
┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────▶│ Prompt  │────▶│   LLM   │────▶ Output
└─────────┘     └─────────┘     └─────────┘

Avec Memory:
┌─────────┐     ┌──────────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────▶│   History    │────▶│ Prompt  │────▶│   LLM   │────▶ Output
└─────────┘     │  Injection   │     └─────────┘     └─────────┘     └─────────┘
                └──────────────┘
                       ▲                    │
                       │                    ▼
                ┌──────────────┐     ┌──────────────┐
                │   Store      │◀────│ Save History │
                │ (session_id) │     └──────────────┘
                └──────────────┘
```

---

## 🔍 Ce qui se passe vraiment

### Étape 1 : Définition du Pipeline

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder(variable_name="history"),  # ⚠️ Placeholder
    ("human", "{input}")
])

chain = prompt | model | StrOutputParser()
```

**Important** : `MessagesPlaceholder(variable_name="history")` crée un **trou** dans le prompt où l'historique sera injecté.

### Étape 2 : Création du Store

```python
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
```

Chaque `session_id` a son propre **historique isolé**. C'est comme avoir plusieurs conversations parallèles.

### Étape 3 : Wrapping avec Memory

```python
chain_with_memory = RunnableWithMessageHistory(
    chain,                      # Pipeline à wrapper
    get_session_history,        # Fonction pour récupérer l'historique
    input_messages_key="input", # Clé de l'input utilisateur
    history_messages_key="history" # Clé pour l'historique dans le prompt
)
```

### Étape 4 : Appel avec session_id

```python
response = chain_with_memory.invoke(
    {"input": "Hello"},
    config={"configurable": {"session_id": "user1"}}
)
```

---

## 🔄 Architecture du Flux (Détaillé)

### Premier Appel (Historique vide)

```
1. User invoque avec session_id="user1"
   └─▶ RunnableWithMessageHistory intercepte

2. Récupération de l'historique
   └─▶ get_session_history("user1")
   └─▶ Crée InMemoryChatMessageHistory() (vide)
   └─▶ Retourne []

3. Construction du prompt
   └─▶ System: "You are helpful."
   └─▶ History: [] (vide)
   └─▶ Human: "Hello"

4. Appel du pipeline
   └─▶ Prompt → Model → Parser
   └─▶ Réponse: "Hi! How can I help?"

5. Sauvegarde dans l'historique
   └─▶ Ajoute HumanMessage("Hello")
   └─▶ Ajoute AIMessage("Hi! How can I help?")
   └─▶ Store["user1"] contient maintenant 2 messages
```

### Deuxième Appel (Avec historique)

```
1. User invoque avec session_id="user1"
   └─▶ RunnableWithMessageHistory intercepte

2. Récupération de l'historique
   └─▶ get_session_history("user1")
   └─▶ Retourne [HumanMessage("Hello"), AIMessage("Hi! How can I help?")]

3. Construction du prompt
   └─▶ System: "You are helpful."
   └─▶ History: [
         HumanMessage("Hello"),
         AIMessage("Hi! How can I help?")
       ]
   └─▶ Human: "What did I say?"

4. Appel du pipeline
   └─▶ Le LLM voit maintenant TOUT l'historique
   └─▶ Réponse: "You said 'Hello'."

5. Sauvegarde dans l'historique
   └─▶ Ajoute HumanMessage("What did I say?")
   └─▶ Ajoute AIMessage("You said 'Hello'.")
   └─▶ Store["user1"] contient maintenant 4 messages
```

---

## ⚠️ Points Critiques

### 1. MessagesPlaceholder est OBLIGATOIRE

```python
# ✅ CORRECT
prompt = ChatPromptTemplate.from_messages([
    ("system", "..."),
    MessagesPlaceholder(variable_name="history"),  # ⚠️ Présent
    ("human", "{input}")
])

# ❌ INCORRECT - La memory ne sera pas injectée
prompt = ChatPromptTemplate.from_messages([
    ("system", "..."),
    ("human", "{input}")  # Pas de MessagesPlaceholder
])
```

### 2. Le session_id doit être dans config

```python
# ✅ CORRECT
chain_with_memory.invoke(
    {"input": "Hello"},
    config={"configurable": {"session_id": "user1"}}
)

# ❌ INCORRECT - Pas de session_id = erreur
chain_with_memory.invoke({"input": "Hello"})
```

### 3. Isolation des Sessions

```python
# Session Alice
chain_with_memory.invoke(
    {"input": "Je suis Alice"},
    config={"configurable": {"session_id": "alice"}}
)

# Session Bob (mémoire complètement isolée)
chain_with_memory.invoke(
    {"input": "Je suis Bob"},
    config={"configurable": {"session_id": "bob"}}
)

# Alice et Bob ont des historiques séparés
# store["alice"] ≠ store["bob"]
```

### 4. Pipeline Complexe Compatible

```python
# Même avec un pipeline complexe, ça fonctionne !
chain = (
    prompt 
    | model 
    | StrOutputParser() 
    | formatter 
    | validator
)

chain_with_memory = RunnableWithMessageHistory(
    chain,  # Pipeline complexe OK
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

---

## 🚀 Pour la Production

### InMemoryChatMessageHistory (Développement)

```python
from langchain_core.chat_history import InMemoryChatMessageHistory

# ✅ Simple, mais perdu au redémarrage
store[session_id] = InMemoryChatMessageHistory()
```

### RedisChatMessageHistory (Production)

```python
from langchain_community.chat_message_histories import RedisChatMessageHistory

def get_session_history(session_id: str):
    return RedisChatMessageHistory(
        session_id=session_id,
        url="redis://localhost:6379"
    )
```

### PostgresChatMessageHistory (Production)

```python
from langchain_community.chat_message_histories import PostgresChatMessageHistory

def get_session_history(session_id: str):
    return PostgresChatMessageHistory(
        session_id=session_id,
        connection_string="postgresql://user:pass@localhost/db"
    )
```

---

## 📊 Comparaison : Avant vs Après

### Avant (ConversationChain - Déprécié)

```python
# ❌ Ancienne méthode (dépréciée)
from langchain.chains import ConversationChain

chain = ConversationChain(
    llm=llm,
    memory=ConversationBufferMemory()
)
```

**Problèmes** :
- ❌ Pas compatible avec LCEL
- ❌ Moins flexible
- ❌ Déprécié

### Après (RunnableWithMessageHistory - Moderne)

```python
# ✅ Nouvelle méthode (LCEL)
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

**Avantages** :
- ✅ Compatible LCEL
- ✅ Flexible et extensible
- ✅ Multi-session natif
- ✅ Production-ready

---

## 🎓 Résumé

1. **`RunnableWithMessageHistory`** wrap ton pipeline LCEL
2. **`MessagesPlaceholder`** crée un trou pour l'historique
3. **`session_id`** isole les conversations
4. L'historique est **automatiquement** injecté et sauvegardé
5. Compatible avec **n'importe quel pipeline LCEL**

**C'est tout !** 🎉
