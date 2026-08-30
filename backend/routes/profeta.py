@profeta_bp.route('/hoy', methods=['GET'])
def partidos_hoy():
    """Devuelve TODOS los partidos disponibles, priorizando colombianos."""
    try:
        hoy_bogota = obtener_fecha_hoy_bogota()
        manana_bogota = obtener_fecha_manana_bogota()
        
        print(f"\n{'='*60}")
        print(f"📅 FECHA HOY Colombia: {hoy_bogota}")
        print(f"📅 FECHA MAÑANA Colombia: {manana_bogota}")
        print(f"{'='*60}")
        
        # Obtener partidos de HOY
        resultado_hoy = obtener_partidos_del_dia(hoy_bogota)
        print(f"\n🔍 API HOY - Success: {resultado_hoy['success']}, Total: {resultado_hoy['total']}")
        
        # Obtener partidos de MAÑANA
        resultado_manana = obtener_partidos_del_dia(manana_bogota)
        print(f"🔍 API MAÑANA - Success: {resultado_manana['success']}, Total: {resultado_manana['total']}")
        
        todos_los_partidos = []
        if resultado_hoy['success'] and resultado_hoy['partidos']:
            todos_los_partidos.extend(resultado_hoy['partidos'])
            print(f"✅ Agregados {len(resultado_hoy['partidos'])} partidos de hoy")
        
        if resultado_manana['success'] and resultado_manana['partidos']:
            todos_los_partidos.extend(resultado_manana['partidos'])
            print(f"✅ Agregados {len(resultado_manana['partidos'])} partidos de mañana")
        
        print(f"\n📊 TOTAL PARTIDOS ENCONTRADOS: {len(todos_los_partidos)}")
        
        # IDs de ligas
        ids_colombianas = ['4497', '5183']  # Liga BetPlay y Copa BetPlay
        ids_prioritarias = [str(liga['id']) for liga in LIGAS_PRIORITARIAS.values()]
        
        # Debug: Mostrar qué ligas se encontraron
        if todos_los_partidos:
            print(f"\n🏆 LIGAS ENCONTRADAS:")
            ligas_encontradas = {}
            for p in todos_los_partidos:
                liga_id = str(p.get('idLeague', 'Unknown'))
                liga_nombre = p.get('strLeague', 'Unknown')
                if liga_id not in ligas_encontradas:
                    ligas_encontradas[liga_id] = liga_nombre
                    es_colombiana = "🇨🇴 COLOMBIANA" if liga_id in ids_colombianas else ""
                    print(f"   - {liga_id}: {liga_nombre} {es_colombiana}")
        
        # Separar programados de finalizados
        partidos_programados = [p for p in todos_los_partidos if p.get('strStatus') != 'FT']
        partidos_finalizados = [p for p in todos_los_partidos if p.get('strStatus') == 'FT']
        
        print(f"\n✅ Programados: {len(partidos_programados)}")
        print(f"✅ Finalizados: {len(partidos_finalizados)}")
        
        # MOSTRAR TODOS LOS PARTIDOS PROGRAMADOS (sin filtrar por fecha)
        partidos_finales = []
        
        # 1. Colombianos programados PRIMERO
        colombianos = [p for p in partidos_programados if str(p.get('idLeague')) in ids_colombianas]
        if colombianos:
            print(f"\n🇨🇴 ENCONTRADOS {len(colombianos)} PARTIDOS COLOMBIANOS!")
            for p in colombianos:
                local = p.get('strHomeTeam', 'Unknown')
                visita = p.get('strAwayTeam', 'Unknown')
                fecha = p.get('dateEvent', 'Unknown')
                hora = p.get('strTime', 'Unknown')
                print(f"   ⚽ {local} vs {visita} - {fecha} {hora}")
        partidos_finales.extend(colombianos)
        
        # 2. Otros prioritarios (máximo 10)
        if len(partidos_finales) < 15:
            otros = [
                p for p in partidos_programados 
                if str(p.get('idLeague')) in ids_prioritarias 
                and str(p.get('idLeague')) not in ids_colombianas
            ]
            partidos_finales.extend(otros[:15-len(partidos_finales)])
            print(f"🌍 Agregados {len(otros[:15-len(partidos_finales)])} partidos internacionales")
        
        # 3. Si no hay programados, mostrar finalizados de hoy
        if not partidos_finales and partidos_finalizados:
            print(f"️ No hay programados, mostrando {len(partidos_finalizados)} finalizados")
            partidos_finales = partidos_finalizados[:15]
        
        # Guardar en caché
        for partido in partidos_finales:
            guardar_partido_cache(partido)
        
        print(f"\n🎯 TOTAL MOSTRANDO: {len(partidos_finales)} partidos")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'fecha_hoy': hoy_bogota,
            'fecha_manana': manana_bogota,
            'total_encontrados': len(todos_los_partidos),
            'total_mostrando': len(partidos_finales),
            'partidos': partidos_finales,
            'debug': {
                'colombianos_encontrados': len(colombianos),
                'api_hoy_success': resultado_hoy['success'],
                'api_hoy_total': resultado_hoy['total'],
                'api_manana_success': resultado_manana['success'],
                'api_manana_total': resultado_manana['total'],
                'ligas_encontradas': ligas_encontradas if todos_los_partidos else {}
            }
        })
    except Exception as e:
        print(f"❌ Error en /hoy: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
