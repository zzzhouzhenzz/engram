"""SessionStart hook — prints engram context for Claude."""

from engram import db


def main():
    db.init_db()
    keywords = db.get_all_keywords()
    recent = db.get_recent(3)

    print("[Engram] Cross-session knowledge persistence is active.")

    if keywords:
        print(f"Available keywords: {', '.join(keywords)}")
        print("Use query_knowledge() when you encounter a relevant situation.")
    else:
        print("No knowledge stored yet.")

    if recent:
        print("\nRecent learnings:")
        for e in recent:
            kws = e.get("keywords", [])
            if isinstance(kws, str):
                kws = [kws]
            print(f"  - {e.get('situation', 'N/A')} [{', '.join(kws)}]")

    print("\nUse save_knowledge() when you solve non-trivial problems.")


if __name__ == "__main__":
    main()
