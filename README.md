# 🔥 Memory dans Pipeline LCEL - Guide Complet

Ce projet démontre comment intégrer proprement la **mémoire conversationnelle** dans un pipeline LCEL en utilisant `RunnableWithMessageHistory`.

## 📚 Concepts Clés

### Pourquoi `RunnableWithMessageHistory` ?

En LCEL, la mémoire ne s'ajoute **PAS** comme avant avec `ConversationChain`. On utilise :

- **`RunnableWithMessageHistory`** : Wrapper qui injecte automatiquement l'historique
- **`MessagesPlaceholder`** : Placeholder dans le prompt pour recevoir l'historique
- **`session_id`** : Identifiant unique pour isoler les conversations

### Schéma Mental

**Sans memory :**
```
User → Prompt → LLM → Output
```

**Avec memory :**
```
User → [History Injection] → Prompt → LLM → Save History → Output
```

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer un fichier .env avec votre clé API
echo "OPENAI_API_KEY=your_key_here" > .env
```

## 📖 Exemples Inclus

### 1. Assistant de Voyage
Démontre comment l'assistant se souvient du nom et du budget de l'utilisateur à travers plusieurs tours de conversation.

### 2. Correcteur de Grammaire
Un professeur strict qui se souvient des erreurs récurrentes de l'étudiant.

### 3. Pipeline Complexe
Exemple avec un pipeline LCEL multi-étapes (Prompt → Model → Parser → Formatter) + memory.

### 4. Multi-Session
Démontre l'isolation des mémoires entre différentes sessions (plusieurs utilisateurs).

## 🎯 Exécution

```bash
python lcel_memory_example.py
```

## 🧠 Comment ça fonctionne ?

### Étape par étape

1. **Création du pipeline LCEL** :
```python
chain = prompt | model | StrOutputParser()
```

2. **Définition du stockage mémoire** :
```python
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
```

3. **Wrapping avec memory** :
```python
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

4. **Utilisation avec session_id** :
```python
response = chain_with_memory.invoke(
    {"input": "Hello"},
    config={"configurable": {"session_id": "user1"}}
)
```

### ⚠️ Points Importants

- **`MessagesPlaceholder(variable_name="history")`** doit être présent dans le prompt
- Chaque `session_id` a sa propre mémoire isolée
- La mémoire est automatiquement injectée et sauvegardée à chaque appel

## 🔧 Pour la Production

Pour un vrai SaaS / agent multi-user, remplacez `InMemoryChatMessageHistory` par :

- `RedisChatMessageHistory` (pour Redis)
- `PostgresChatMessageHistory` (pour PostgreSQL)
- `MongoDBChatMessageHistory` (pour MongoDB)

## 📝 Structure du Code

```
.
├── lcel_memory_example.py  # Exemples complets
├── requirements.txt         # Dépendances
├── README.md               # Ce fichier
└── .env                    # Variables d'environnement (à créer)
```

## 🎓 Apprentissage

Après avoir testé les exemples, réfléchissez à :

1. ✅ L'assistant reste-t-il dans son rôle ?
2. ✅ Se souvient-il correctement des détails passés ?
3. ✅ Que se passe-t-il si la mémoire est effacée ou réinitialisée ?
4. ✅ Comment isoler les conversations entre utilisateurs ?

## 📚 Ressources

- [LangChain LCEL Documentation](https://python.langchain.com/docs/expression_language/)
- [RunnableWithMessageHistory](https://python.langchain.com/docs/how_to/message_history/)
- [Chat Memory Types](https://python.langchain.com/docs/modules/memory/)
