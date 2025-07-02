#!/usr/bin/env python3
"""
Elasticsearch CLI für Steam Price Tracker
Kommandozeilen-Tool für Elasticsearch-Management
"""

import argparse
import sys
from pathlib import Path

# Steam Price Tracker Module importieren
sys.path.insert(0, str(Path.cwd()))

def cmd_setup(args):
    """Elasticsearch Setup ausführen"""
    try:
        from elasticsearch_manager import setup_elasticsearch_for_steam_tracker
        from database_manager import DatabaseManager
        
        # Database Manager
        db_manager = DatabaseManager(args.db_path)
        
        # Elasticsearch Setup
        result = setup_elasticsearch_for_steam_tracker(
            db_manager, 
            host=args.host, 
            port=args.port,
            username=args.username,
            password=args.password
        )
        
        if result['success']:
            print("✅ Elasticsearch Setup erfolgreich!")
            print(f"   📊 {result['indices_created']} Indizes erstellt")
            print(f"   📋 {result['mappings_applied']} Mappings angewendet")
        else:
            print(f"❌ Setup fehlgeschlagen: {result['error']}")
            
    except ImportError:
        print("❌ elasticsearch_manager Modul nicht gefunden")
        print("💡 Installiere Elasticsearch: pip install -r requirements-elasticsearch.txt")
    except Exception as e:
        print(f"❌ Setup-Fehler: {e}")

def cmd_export(args):
    """Daten zu Elasticsearch exportieren"""
    try:
        from elasticsearch_manager import create_elasticsearch_manager
        from database_manager import DatabaseManager
        
        # Elasticsearch Manager
        es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
        if not es_manager:
            print("❌ Elasticsearch-Verbindung fehlgeschlagen")
            return
        
        # Database Manager
        db_manager = DatabaseManager(args.db_path)
        
        # Export
        print("🚀 Starte Datenexport...")
        export_stats = es_manager.export_sqlite_to_elasticsearch(db_manager)
        
        print(f"✅ Export abgeschlossen:")
        print(f"   📊 Price Snapshots: {export_stats['price_snapshots']}")
        print(f"   📱 Tracked Apps: {export_stats['tracked_apps']}")
        print(f"   🔤 Name History: {export_stats['name_history']}")
        print(f"   📈 Charts: {export_stats['charts_tracking']}")
        print(f"   💰 Charts Prices: {export_stats['charts_prices']}")
        print(f"   📊 Statistiken: {export_stats['statistics']}")
        print(f"   🎯 Gesamt: {export_stats['total_exported']}")
        
    except Exception as e:
        print(f"❌ Export-Fehler: {e}")

def cmd_status(args):
    """Elasticsearch-Status anzeigen"""
    try:
        from elasticsearch_manager import create_elasticsearch_manager
        
        es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
        if not es_manager:
            print("❌ Elasticsearch-Verbindung fehlgeschlagen")
            return
        
        # Health Check
        health = es_manager.health_check()
        
        if health['connection_ok']:
            print("✅ Elasticsearch-Status:")
            print(f"   🔗 Cluster: {health['cluster_name']}")
            print(f"   📊 Status: {health['cluster_status']}")
            print(f"   🖥️ Nodes: {health['number_of_nodes']}")
            print(f"   📁 Shards: {health['active_shards']}")
            print(f"   📄 Dokumente: {health['total_documents']}")
            
            print("\n📋 Index-Details:")
            for name, stats in health['indices'].items():
                if stats['exists']:
                    print(f"   • {stats['index_name']}: {stats['document_count']} Dokumente")
                else:
                    print(f"   • {stats['index_name']}: nicht vorhanden")
        else:
            print(f"❌ Elasticsearch nicht erreichbar: {health['error']}")
            
    except Exception as e:
        print(f"❌ Status-Fehler: {e}")

def cmd_reset(args):
    """Elasticsearch-Indizes zurücksetzen"""
    try:
        from elasticsearch_manager import create_elasticsearch_manager
        
        es_manager = create_elasticsearch_manager(args.host, args.port, args.username, args.password)
        if not es_manager:
            print("❌ Elasticsearch-Verbindung fehlgeschlagen")
            return
        
        if not args.force:
            confirm = input("⚠️ WARNUNG: Alle Steam Price Tracker Indizes werden gelöscht! Fortfahren? (ja/nein): ")
            if confirm.lower() not in ['ja', 'j', 'yes', 'y']:
                print("❌ Abgebrochen")
                return
        
        # Indizes löschen
        deleted = es_manager.delete_all_indices()
        print(f"🗑️ {deleted} Indizes gelöscht")
        
        # Neue Indizes erstellen
        created = es_manager.create_indices_and_mappings()
        print(f"✅ {created} neue Indizes erstellt")
        
    except Exception as e:
        print(f"❌ Reset-Fehler: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Elasticsearch CLI für Steam Price Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Globale Argumente
    parser.add_argument('--host', default='localhost', help='Elasticsearch Host')
    parser.add_argument('--port', type=int, default=9200, help='Elasticsearch Port')
    parser.add_argument('--username', help='Elasticsearch Username')
    parser.add_argument('--password', help='Elasticsearch Password')
    parser.add_argument('--db-path', default='steam_price_tracker.db', help='SQLite Datenbank Pfad')
    
    subparsers = parser.add_subparsers(dest='command', help='Kommandos')
    
    # Setup Command
    setup_parser = subparsers.add_parser('setup', help='Vollständiges Elasticsearch Setup')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Export Command
    export_parser = subparsers.add_parser('export', help='Daten zu Elasticsearch exportieren')
    export_parser.set_defaults(func=cmd_export)
    
    # Status Command
    status_parser = subparsers.add_parser('status', help='Elasticsearch-Status anzeigen')
    status_parser.set_defaults(func=cmd_status)
    
    # Reset Command
    reset_parser = subparsers.add_parser('reset', help='Elasticsearch-Indizes zurücksetzen')
    reset_parser.add_argument('--force', action='store_true', help='Ohne Bestätigung ausführen')
    reset_parser.set_defaults(func=cmd_reset)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n⏹️ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    main()
