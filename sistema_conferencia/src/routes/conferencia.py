from flask import Blueprint, request, jsonify, send_file
from src.models.rastreio import db, RastreioEsperado, MercadoriaConferida, DashboardCache
from datetime import datetime, date
import io
import csv
import os
import json

conferencia_bp = Blueprint('conferencia', __name__)

@conferencia_bp.route('/rastreios/importar', methods=['POST'])
def importar_rastreios():
    """Importa uma lista de códigos de rastreio para a base"""
    try:
        data = request.get_json()
        if not data or 'rastreios' not in data:
            return jsonify({'erro': 'Lista de rastreios é obrigatória'}), 400
        
        rastreios = data['rastreios']
        if not isinstance(rastreios, list):
            return jsonify({'erro': 'Rastreios deve ser uma lista'}), 400
        
        # Limpar base existente se solicitado
        if data.get('limpar_base', False):
            db.session.query(RastreioEsperado).delete()
            db.session.query(MercadoriaConferida).delete()
        
        novos_rastreios = 0
        duplicados = 0
        
        for codigo in rastreios:
            if not codigo or not isinstance(codigo, str):
                continue
                
            codigo = codigo.strip().upper()
            if not codigo:
                continue
                
            # Verificar se já existe
            existe = RastreioEsperado.query.filter_by(codigo_rastreio=codigo).first()
            if existe:
                duplicados += 1
                continue
            
            # Criar novo rastreio
            novo_rastreio = RastreioEsperado(codigo_rastreio=codigo)
            db.session.add(novo_rastreio)
            novos_rastreios += 1
        
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Importação concluída. {novos_rastreios} novos rastreios adicionados.',
            'novos': novos_rastreios,
            'duplicados': duplicados
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao importar rastreios: {str(e)}'}), 500

@conferencia_bp.route('/mercadorias/bipar', methods=['POST'])
def bipar_mercadoria():
    """Registra uma mercadoria bipada e verifica seu status"""
    try:
        data = request.get_json()
        if not data or 'codigo_rastreio' not in data:
            return jsonify({'erro': 'Código de rastreio é obrigatório'}), 400
        
        codigo = data['codigo_rastreio'].strip().upper()
        if not codigo:
            return jsonify({'erro': 'Código de rastreio não pode estar vazio'}), 400
        
        # Verificar se o rastreio está na base
        rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=codigo).first()
        
        if not rastreio:
            # Registrar como não encontrado
            mercadoria_conferida = MercadoriaConferida(
                codigo_rastreio=codigo,
                data_bipagem=datetime.now().date()
            )
            db.session.add(mercadoria_conferida)
            db.session.commit()
            
            # Incrementar dashboard mesmo para rastreios não encontrados
            try:
                hoje = datetime.now().date()
                cache = DashboardCache.query.filter_by(data=hoje).first()
                
                # Verificar se este rastreio já foi contado no dashboard hoje
                rastreios_contados = json.loads(cache.rastreios_contados) if cache and cache.rastreios_contados else []
                
                if codigo not in rastreios_contados:
                    if cache:
                        # Incrementar contadores existentes
                        cache.total_hoje += 1
                        cache.sem_status_hoje += 1  # Não encontrado = sem status
                        
                        # A transportadora será atualizada posteriormente através das funções de atualização
                        # Por enquanto, apenas incrementar o total e status
                        
                        # Adicionar à lista de rastreios contados
                        if not cache.rastreios_contados:
                            cache.rastreios_contados = '[]'
                        rastreios_contados = json.loads(cache.rastreios_contados)
                        rastreios_contados.append(codigo)
                        cache.rastreios_contados = json.dumps(rastreios_contados)
                        
                        cache.ultima_atualizacao = datetime.now()
                        db.session.commit()
                    else:
                        # Se não existe cache, criar novo
                        transportadoras = {
                            'J&T': 0, 'JADLOG': 0, 'DIALOGO': 0, 'CORREIOS': 0, 'CORREIOS PA': 0,
                            'LOGAN': 0, 'FAVELA LOG': 0, 'SAC SERVICE': 0, 'DISSUDES': 0
                        }
                        
                        # A transportadora será atualizada posteriormente através das funções de atualização
                        # Por enquanto, apenas incrementar o total e status
                        
                        cache = DashboardCache(
                            data=hoje,
                            transportadoras=transportadoras,
                            total_hoje=1,
                            coleta_hoje=0,
                            insucesso_hoje=0,
                            sem_status_hoje=1,  # Não encontrado = sem status
                            rastreios_contados=json.dumps([codigo]),
                            ultima_atualizacao=datetime.now()
                        )
                        db.session.add(cache)
                        db.session.commit()
                else:
                    print(f"Rastreio {codigo} já foi contado no dashboard hoje")
                    
            except Exception as dashboard_error:
                # Se houver erro no dashboard, não afetar a bipagem
                print(f"Erro ao incrementar dashboard após bipagem: {dashboard_error}")
            
            return jsonify({
                'mensagem': 'Mercadoria não encontrada na base de rastreios',
                'status': 'nao_encontrado',
                'codigo': codigo
            })
        
        # Verificar se já foi conferida
        ja_conferida = MercadoriaConferida.query.filter_by(codigo_rastreio=codigo).first()
        if ja_conferida:
            return jsonify({
                'mensagem': 'Mercadoria já foi conferida anteriormente',
                'timestamp_anterior': ja_conferida.timestamp.isoformat()
            })
        
        # Registrar como conferida
        mercadoria_conferida = MercadoriaConferida(
            codigo_rastreio=codigo,
            data_bipagem=datetime.now().date()
        )
        db.session.add(mercadoria_conferida)
        
        # Atualizar status do rastreio apenas se ainda for 'pendente'
        if rastreio.status == 'pendente':
            rastreio.status = 'conferido'
        
        db.session.commit()
        
        # Incrementar dashboard após bipagem (apenas se não foi contado antes)
        try:
            hoje = datetime.now().date()
            cache = DashboardCache.query.filter_by(data=hoje).first()
            
            # Verificar se este rastreio já foi contado no dashboard hoje
            rastreios_contados = json.loads(cache.rastreios_contados) if cache and cache.rastreios_contados else []
            
            if codigo not in rastreios_contados:
                if cache:
                    # Incrementar contadores existentes
                    cache.total_hoje += 1
                    
                    # Verificar status atual do rastreio para incrementar o contador correto
                    if rastreio.status == 'coleta':
                        cache.coleta_hoje += 1
                    elif rastreio.status == 'insucesso':
                        cache.insucesso_hoje += 1
                    else:
                        cache.sem_status_hoje += 1  # pendente, conferido, etc.
                    
                    # A transportadora será atualizada posteriormente através das funções de atualização
                    # Por enquanto, apenas incrementar o total e status
                    
                    # Adicionar à lista de rastreios contados
                    if not cache.rastreios_contados:
                        cache.rastreios_contados = '[]'
                    rastreios_contados = json.loads(cache.rastreios_contados)
                    rastreios_contados.append(codigo)
                    cache.rastreios_contados = json.dumps(rastreios_contados)
                    
                    cache.ultima_atualizacao = datetime.now()
                    db.session.commit()
                else:
                    # Se não existe cache, criar novo
                    transportadoras = {
                        'J&T': 0, 'JADLOG': 0, 'DIALOGO': 0, 'CORREIOS': 0, 'CORREIOS PA': 0,
                        'LOGAN': 0, 'FAVELA LOG': 0, 'SAC SERVICE': 0, 'DISSUDES': 0
                    }
                    
                    # Verificar status atual do rastreio para o contador inicial
                    coleta_inicial = 1 if rastreio.status == 'coleta' else 0
                    insucesso_inicial = 1 if rastreio.status == 'insucesso' else 0
                    sem_status_inicial = 1 if rastreio.status not in ['coleta', 'insucesso'] else 0
                    
                    # A transportadora será atualizada posteriormente através das funções de atualização
                    # Por enquanto, apenas incrementar o total e status
                    
                    cache = DashboardCache(
                        data=hoje,
                        transportadoras=transportadoras,
                        total_hoje=1,
                        coleta_hoje=coleta_inicial,
                        insucesso_hoje=insucesso_inicial,
                        sem_status_hoje=sem_status_inicial,
                        rastreios_contados=json.dumps([codigo]),
                        ultima_atualizacao=datetime.now()
                    )
                    db.session.add(cache)
                    db.session.commit()
            else:
                print(f"Rastreio {codigo} já foi contado no dashboard hoje")
                
        except Exception as dashboard_error:
            # Se houver erro no dashboard, não afetar a bipagem
            print(f"Erro ao incrementar dashboard após bipagem: {dashboard_error}")
        
        return jsonify({
            'mensagem': 'Mercadoria conferida com sucesso',
            'status': 'encontrado',
            'codigo': codigo
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao bipar mercadoria: {str(e)}'}), 500

@conferencia_bp.route('/mercadorias/faltantes', methods=['GET'])
def listar_faltantes():
    """Retorna a lista de mercadorias faltantes"""
    try:
        # Apenas rastreios pendentes são considerados faltantes
        faltantes = RastreioEsperado.query.filter_by(status='pendente').all()
        
        lista_faltantes = []
        for rastreio in faltantes:
            lista_faltantes.append({
                'codigo': rastreio.codigo_rastreio,
                'status': rastreio.status
            })
        
        return jsonify({
            'faltantes': lista_faltantes,
            'total': len(lista_faltantes)
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar faltantes: {str(e)}'}), 500

@conferencia_bp.route('/mercadorias/conferidas', methods=['GET'])
def listar_conferidas():
    """Retorna a lista de mercadorias já conferidas"""
    try:
        conferidas = MercadoriaConferida.query.all()
        
        lista_conferidas = []
        for mercadoria in conferidas:
            # Verificar se estava na base
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            status_base = 'na_base' if rastreio else 'fora_da_base'
            
            lista_conferidas.append({
                'codigo': mercadoria.codigo_rastreio,
                'timestamp': mercadoria.timestamp.isoformat(),
                'status_base': status_base,
                'transportadora': mercadoria.transportadora
            })
        
        return jsonify({
            'conferidas': lista_conferidas,
            'total': len(lista_conferidas)
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao listar conferidas: {str(e)}'}), 500

@conferencia_bp.route("/rastreios/resetar", methods=["POST"])
def resetar_sistema():
    """Reseta o sistema: apaga rastreios esperados e TODAS as mercadorias conferidas/bipadas. NÃO afeta o dashboard."""
    try:
        # Contagens antes da limpeza
        total_rastreios = RastreioEsperado.query.count()
        total_mercadorias = MercadoriaConferida.query.count()
        
        # Limpar rastreios esperados e TODAS as mercadorias conferidas/bipadas
        db.session.query(RastreioEsperado).delete()
        db.session.query(MercadoriaConferida).delete()
        
        # NÃO limpar o cache do dashboard - manter os contadores do dia
        # O dashboard continuará mostrando os dados do dia mesmo após o reset
        
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Sistema resetado com sucesso! {total_rastreios} rastreios esperados e {total_mercadorias} mercadorias (bipadas/conferidas) foram removidos. O dashboard do dia foi mantido.',
            'rastreios_removidos': total_rastreios,
            'mercadorias_removidas': total_mercadorias,
            'dashboard_mantido': True
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao resetar sistema: {str(e)}'}), 500

@conferencia_bp.route("/dashboard/resetar", methods=["POST"])
def resetar_dashboard():
    """Reseta apenas o cache do dashboard do dia"""
    try:
        hoje = datetime.now().date()
        
        # Buscar cache do dia
        cache = DashboardCache.query.filter_by(data=hoje).first()
        
        if not cache:
            return jsonify({'mensagem': 'Nenhum cache do dashboard encontrado para hoje'})
        
        # Remover cache
        db.session.delete(cache)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Cache do dashboard do dia resetado com sucesso.',
            'cache_removido': True,
            'data': hoje.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao resetar dashboard: {str(e)}'}), 500

@conferencia_bp.route('/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Retorna estatísticas do sistema"""
    try:
        total_esperados = RastreioEsperado.query.count()
        
        # Contar rastreios que foram processados (conferido, coleta, insucesso)
        total_conferidos = db.session.query(RastreioEsperado).filter(
            RastreioEsperado.status.in_(['conferido', 'coleta', 'insucesso'])
        ).count()
        
        total_pendentes = RastreioEsperado.query.filter_by(status='pendente').count()
        
        # Contar mercadorias bipadas que não estão na base
        total_fora_base = MercadoriaConferida.query.join(
            RastreioEsperado, 
            MercadoriaConferida.codigo_rastreio == RastreioEsperado.codigo_rastreio,
            isouter=True
        ).filter(RastreioEsperado.id.is_(None)).count()
        
        # Total de mercadorias bipadas (incluindo fora da base)
        total_bipadas = MercadoriaConferida.query.count()
        
        # Percentual baseado no total de esperados
        percentual_conferido = (total_conferidos / total_esperados * 100) if total_esperados > 0 else 0
        
        return jsonify({
            'total_esperados': total_esperados,
            'total_conferidos': total_conferidos,
            'total_pendentes': total_pendentes,
            'total_fora_base': total_fora_base,
            'total_bipadas': total_bipadas,
            'percentual_conferido': round(percentual_conferido, 2)
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter estatísticas: {str(e)}'}), 500

@conferencia_bp.route("/mercadorias/bipadas", methods=["GET"])
def listar_bipadas():
    """Retorna a lista de todas as mercadorias bipadas separadas por status"""
    try:
        bipadas = MercadoriaConferida.query.all()
        
        bipadas_coleta = []
        bipadas_insucesso = []
        bipadas_sem_status = []
        
        for mercadoria in bipadas:
            # Verificar se está na base e qual o status
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            
            item = {
                "codigo": mercadoria.codigo_rastreio,
                "timestamp": mercadoria.timestamp.isoformat(),
                "transportadora": mercadoria.transportadora,
                "data_bipagem": mercadoria.data_bipagem.isoformat() if mercadoria.data_bipagem else None
            }
            
            if rastreio:
                if rastreio.status == 'coleta':
                    bipadas_coleta.append(item)
                elif rastreio.status == 'insucesso':
                    bipadas_insucesso.append(item)
                else:
                    bipadas_sem_status.append(item)
            else:
                # Não está na base
                bipadas_sem_status.append(item)
        
        return jsonify({
            "bipadas_coleta": bipadas_coleta,
            "bipadas_insucesso": bipadas_insucesso,
            "bipadas_sem_status": bipadas_sem_status,
            "total_coleta": len(bipadas_coleta),
            "total_insucesso": len(bipadas_insucesso),
            "total_sem_status": len(bipadas_sem_status),
            "total": len(bipadas)
        })
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar mercadorias bipadas: {str(e)}"}), 500

@conferencia_bp.route("/rastreios/status", methods=["POST"])
def aplicar_status():
    """Aplica um status específico a um rastreio"""
    try:
        data = request.get_json()
        if not data or "codigo_rastreio" not in data or "status" not in data:
            return jsonify({"erro": "Código de rastreio e status são obrigatórios"}), 400
        
        codigo = data["codigo_rastreio"].strip().upper()
        status = data["status"].strip().lower()
        
        if status not in ["coleta", "insucesso", "pendente", "conferido"]:
            return jsonify({"erro": "Status inválido"}), 400
        
        # Buscar o rastreio
        rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=codigo).first()
        
        if not rastreio:
            return jsonify({"erro": "Rastreio não encontrado na base"}), 404
        
        # Atualizar status
        rastreio.status = status
        db.session.commit()
        
        return jsonify({
            "mensagem": f"Status '{status}' aplicado ao rastreio {codigo}",
            "codigo": codigo,
            "status": status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao aplicar status: {str(e)}"}), 500

@conferencia_bp.route("/mercadorias/bipadas/<status>", methods=["GET"])
def listar_bipadas_por_status(status):
    """Retorna a lista de mercadorias bipadas por status específico"""
    try:
        if status not in ["coleta", "insucesso", "sem_status"]:
            return jsonify({"erro": "Status inválido"}), 400
        
        bipadas = MercadoriaConferida.query.all()
        lista_bipadas = []
        
        for mercadoria in bipadas:
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            
            if status == "sem_status":
                if not rastreio or rastreio.status not in ["coleta", "insucesso"]:
                    lista_bipadas.append({
                        "codigo": mercadoria.codigo_rastreio,
                        "timestamp": mercadoria.timestamp.isoformat(),
                        "transportadora": mercadoria.transportadora,
                        "data_bipagem": mercadoria.data_bipagem.isoformat() if mercadoria.data_bipagem else None
                    })
            elif rastreio and rastreio.status == status:
                lista_bipadas.append({
                    "codigo": mercadoria.codigo_rastreio,
                    "timestamp": mercadoria.timestamp.isoformat(),
                    "transportadora": mercadoria.transportadora,
                    "data_bipagem": mercadoria.data_bipagem.isoformat() if mercadoria.data_bipagem else None
                })
        
        return jsonify({
            "bipadas": lista_bipadas,
            "status": status,
            "total": len(lista_bipadas)
        })
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar bipadas por status: {str(e)}"}), 500

@conferencia_bp.route("/dashboard", methods=["GET"])
def obter_dashboard():
    """Retorna dados do dashboard do dia - usa cache se disponível"""
    try:
        hoje = datetime.now().date()
        
        # Tentar buscar do cache primeiro
        cache = DashboardCache.query.filter_by(data=hoje).first()
        
        if cache:
            # Retornar dados do cache
            return jsonify({
                'transportadoras': cache.transportadoras,
                'total_hoje': cache.total_hoje,
                'coleta_hoje': cache.coleta_hoje,
                'insucesso_hoje': cache.insucesso_hoje,
                'sem_status_hoje': cache.sem_status_hoje,
                'cache_info': {
                    'ultima_atualizacao': cache.ultima_atualizacao.isoformat(),
                    'fonte': 'cache'
                }
            })
        
        # Se não há cache, criar cache zerado e forçar recálculo para acumular dados
        resultado = calcular_e_salvar_dashboard(hoje)
        # Forçar recálculo para acumular dados existentes
        resultado_acumulado = forcar_recalculo_dashboard(hoje)
        return jsonify(resultado_acumulado)
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao obter dashboard: {str(e)}'}), 500

def calcular_e_salvar_dashboard(hoje):
    """Calcula e salva o dashboard no cache baseado nas mercadorias conferidas hoje"""
    try:
        # Verificar se já existe cache para hoje
        cache_existente = DashboardCache.query.filter_by(data=hoje).first()
        
        if cache_existente:
            # Se existe cache, NÃO recalcular - apenas retornar os dados existentes
            return {
                'transportadoras': cache_existente.transportadoras,
                'total_hoje': cache_existente.total_hoje,
                'coleta_hoje': cache_existente.coleta_hoje,
                'insucesso_hoje': cache_existente.insucesso_hoje,
                'sem_status_hoje': cache_existente.sem_status_hoje,
                'cache_info': {
                    'ultima_atualizacao': cache_existente.ultima_atualizacao.isoformat(),
                    'fonte': 'cache_preservado'
                }
            }
        
        # Só criar cache zerado se NÃO existir
        transportadoras = {
            'J&T': 0, 'JADLOG': 0, 'DIALOGO': 0, 'CORREIOS': 0, 'CORREIOS PA': 0,
            'LOGAN': 0, 'FAVELA LOG': 0, 'SAC SERVICE': 0, 'DISSUDES': 0
        }
        
        # Criar novo cache zerado
        cache = DashboardCache(
            data=hoje,
            transportadoras=transportadoras,
            total_hoje=0,
            coleta_hoje=0,
            insucesso_hoje=0,
            sem_status_hoje=0,
            rastreios_contados=json.dumps([]),
            ultima_atualizacao=datetime.now()
        )
        db.session.add(cache)
        db.session.commit()
        
        return {
            'transportadoras': transportadoras,
            'total_hoje': 0,
            'coleta_hoje': 0,
            'insucesso_hoje': 0,
            'sem_status_hoje': 0,
            'cache_info': {
                'ultima_atualizacao': cache.ultima_atualizacao.isoformat(),
                'fonte': 'cache_novo_zerado'
            }
        }
        
    except Exception as e:
        db.session.rollback()
        raise e

def forcar_recalculo_dashboard(hoje):
    """Força o recálculo do dashboard preservando histórico e somando novas bipagens"""
    try:
        # Buscar cache existente para preservar histórico
        cache = DashboardCache.query.filter_by(data=hoje).first()
        
        # Se não existe cache, criar um novo zerado
        if not cache:
            transportadoras = {
                'J&T': 0, 'JADLOG': 0, 'DIALOGO': 0, 'CORREIOS': 0, 'CORREIOS PA': 0,
                'LOGAN': 0, 'FAVELA LOG': 0, 'SAC SERVICE': 0, 'DISSUDES': 0
            }
            
            cache = DashboardCache(
                data=hoje,
                transportadoras=transportadoras,
                total_hoje=0,
                coleta_hoje=0,
                insucesso_hoje=0,
                sem_status_hoje=0,
                rastreios_contados=json.dumps([]),
                ultima_atualizacao=datetime.now()
            )
            db.session.add(cache)
            db.session.commit()
        
        # Buscar mercadorias bipadas hoje
        bipadas_hoje = MercadoriaConferida.query.filter_by(data_bipagem=hoje).all()
        
        # Recalcular tudo baseado nas mercadorias bipadas hoje
        total_hoje = len(bipadas_hoje)
        coleta_hoje = 0
        insucesso_hoje = 0
        sem_status_hoje = 0
        transportadoras = {
            'J&T': 0, 'JADLOG': 0, 'DIALOGO': 0, 'CORREIOS': 0, 'CORREIOS PA': 0,
            'LOGAN': 0, 'FAVELA LOG': 0, 'SAC SERVICE': 0, 'DISSUDES': 0
        }
        
        # Contar todas as mercadorias bipadas hoje
        for mercadoria in bipadas_hoje:
            # Contar por transportadora (se tiver transportadora definida)
            if mercadoria.transportadora and mercadoria.transportadora.strip():
                transportadora_nome = mercadoria.transportadora.strip()
                if transportadora_nome in transportadoras:
                    transportadoras[transportadora_nome] += 1
            
            # Verificar se está na base atual para determinar status
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            if rastreio:
                # Se está na base, usar status atual
                if rastreio.status == 'coleta':
                    coleta_hoje += 1
                elif rastreio.status == 'insucesso':
                    insucesso_hoje += 1
                else:
                    sem_status_hoje += 1  # pendente, conferido, etc.
            else:
                # Se não está na base atual, contar como sem status
                sem_status_hoje += 1
        
        # Atualizar cache com dados recalculados
        cache.transportadoras = transportadoras
        cache.total_hoje = total_hoje
        cache.coleta_hoje = coleta_hoje
        cache.insucesso_hoje = insucesso_hoje
        cache.sem_status_hoje = sem_status_hoje
        cache.rastreios_contados = json.dumps([m.codigo_rastreio for m in bipadas_hoje])
        cache.ultima_atualizacao = datetime.now()
        
        db.session.commit()
        
        return {
            'transportadoras': transportadoras,
            'total_hoje': total_hoje,
            'coleta_hoje': coleta_hoje,
            'insucesso_hoje': insucesso_hoje,
            'sem_status_hoje': sem_status_hoje
        }
        
    except Exception as e:
        db.session.rollback()
        raise e

def recalcular_status_dashboard(hoje):
    """Recalcula apenas os status do dashboard preservando outros dados"""
    try:
        cache = DashboardCache.query.filter_by(data=hoje).first()
        
        if cache:
            # Buscar mercadorias bipadas hoje
            bipadas_hoje = MercadoriaConferida.query.filter_by(data_bipagem=hoje).all()
            
            # Recalcular status baseado nas mercadorias atuais
            coleta_hoje = 0
            insucesso_hoje = 0
            sem_status_hoje = 0
            
            for mercadoria in bipadas_hoje:
                rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
                if rastreio:
                    if rastreio.status == 'coleta':
                        coleta_hoje += 1
                    elif rastreio.status == 'insucesso':
                        insucesso_hoje += 1
                    else:
                        sem_status_hoje += 1  # pendente, conferido, etc.
                else:
                    # Se não está na base atual, contar como sem status
                    sem_status_hoje += 1
            
            # Atualizar apenas os status, preservando outros contadores
            cache.coleta_hoje = coleta_hoje
            cache.insucesso_hoje = insucesso_hoje
            cache.sem_status_hoje = sem_status_hoje
            cache.ultima_atualizacao = datetime.now()
            db.session.commit()
            
    except Exception as e:
        db.session.rollback()
        raise e

def recalcular_transportadoras_dashboard(hoje):
    """Recalcula apenas as transportadoras do dashboard preservando outros dados"""
    try:
        cache = DashboardCache.query.filter_by(data=hoje).first()
        
        if cache:
            # Buscar mercadorias bipadas hoje
            bipadas_hoje = MercadoriaConferida.query.filter_by(data_bipagem=hoje).all()
            
            # Recalcular transportadoras baseado nas mercadorias atuais
            transportadoras = {
                'J&T': 0, 'JADLOG': 0, 'DIALOGO': 0, 'CORREIOS': 0, 'CORREIOS PA': 0,
                'LOGAN': 0, 'FAVELA LOG': 0, 'SAC SERVICE': 0, 'DISSUDES': 0
            }
            
            for mercadoria in bipadas_hoje:
                # Contar por transportadora (se tiver transportadora definida)
                if mercadoria.transportadora and mercadoria.transportadora.strip():
                    transportadora_nome = mercadoria.transportadora.strip()
                    if transportadora_nome in transportadoras:
                        transportadoras[transportadora_nome] += 1
            
            # Atualizar apenas as transportadoras, preservando outros contadores
            cache.transportadoras = transportadoras
            cache.ultima_atualizacao = datetime.now()
            db.session.commit()
            
    except Exception as e:
        db.session.rollback()
        raise e

@conferencia_bp.route("/dashboard/atualizar", methods=["POST"])
def atualizar_dashboard():
    """Força a atualização do cache do dashboard"""
    try:
        hoje = datetime.now().date()
        
        # Forçar recálculo
        resultado = forcar_recalculo_dashboard(hoje)
        
        return jsonify({
            'transportadoras': resultado['transportadoras'],
            'total_hoje': resultado['total_hoje'],
            'coleta_hoje': resultado['coleta_hoje'],
            'insucesso_hoje': resultado['insucesso_hoje'],
            'sem_status_hoje': resultado['sem_status_hoje'],
            'cache_info': {
                'ultima_atualizacao': datetime.now().isoformat(),
                'fonte': 'forcado'
            }
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao atualizar dashboard: {str(e)}'}), 500

@conferencia_bp.route("/dashboard/incrementar", methods=["POST"])
def incrementar_dashboard():
    """Incrementa os contadores do dashboard quando uma mercadoria é bipada"""
    try:
        data = request.get_json()
        if not data or 'transportadora' not in data or 'status' not in data:
            return jsonify({'erro': 'Transportadora e status são obrigatórios'}), 400
        
        transportadora = data['transportadora'].strip()
        status = data['status'].strip()
        hoje = datetime.now().date()
        
        # Forçar recálculo completo do dashboard
        resultado = forcar_recalculo_dashboard(hoje)
        
        return jsonify({
            'mensagem': 'Dashboard atualizado com sucesso',
            'total_hoje': resultado['total_hoje'],
            'coleta_hoje': resultado['coleta_hoje'],
            'insucesso_hoje': resultado['insucesso_hoje'],
            'sem_status_hoje': resultado['sem_status_hoje'],
            'transportadoras': resultado['transportadoras']
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao incrementar dashboard: {str(e)}'}), 500

@conferencia_bp.route("/status/atualizar", methods=["POST"])
def atualizar_status():
    """Atualiza o status de uma mercadoria e recalcula o dashboard"""
    try:
        data = request.get_json()
        if not data or 'codigo_rastreio' not in data or 'status' not in data:
            return jsonify({'erro': 'Código de rastreio e status são obrigatórios'}), 400
        
        codigo = data['codigo_rastreio'].strip().upper()
        status = data['status'].strip()
        
        if not codigo or not status:
            return jsonify({'erro': 'Código de rastreio e status não podem estar vazios'}), 400
        
        # Buscar rastreio
        rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=codigo).first()
        
        if not rastreio:
            return jsonify({'erro': 'Rastreio não encontrado'}), 404
        
        # Atualizar status
        rastreio.status = status
        db.session.commit()
        
        # Atualizar dashboard após mudança de status
        try:
            hoje = datetime.now().date()
            recalcular_status_dashboard(hoje)
        except Exception as dashboard_error:
            print(f"Erro ao atualizar dashboard após mudança de status: {dashboard_error}")
        
        return jsonify({
            'mensagem': f'Status atualizado para {status}',
            'codigo': codigo,
            'status': status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao atualizar status: {str(e)}'}), 500

@conferencia_bp.route("/exportar/excel", methods=["POST"])
def exportar_excel():
    """Exporta dados para Excel (CSV) - APENAS mercadorias que estão na base"""
    try:
        data = request.get_json()
        if not data or 'transportadora' not in data:
            return jsonify({'erro': 'Transportadora é obrigatória'}), 400
        
        transportadora = data['transportadora'].strip()
        if not transportadora:
            return jsonify({'erro': 'Transportadora não pode estar vazia'}), 400
        
        # Buscar APENAS mercadorias bipadas que estão na base
        mercadorias_na_base = []
        todas_mercadorias = MercadoriaConferida.query.all()
        
        for mercadoria in todas_mercadorias:
            # Verificar se está na base
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            if rastreio:  # SÓ incluir se estiver na base
                mercadorias_na_base.append(mercadoria)
        
        if not mercadorias_na_base:
            return jsonify({'erro': 'Nenhuma mercadoria bipada na base para exportar'}), 400
        
        # Criar arquivo CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(['Código de Rastreio', 'Data Bipagem', 'Hora Bipagem', 'Transportadora', 'Status'])
        
        # Dados (APENAS as que estão na base)
        for mercadoria in mercadorias_na_base:
            # Verificar status (já sabemos que está na base)
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            status = rastreio.status if rastreio else 'Pendente'
            
            # Formatar data e hora
            data_bipagem = mercadoria.data_bipagem.strftime('%d/%m/%Y') if mercadoria.data_bipagem else 'N/A'
            hora_bipagem = mercadoria.timestamp.strftime('%H:%M:%S') if mercadoria.timestamp else 'N/A'
            
            writer.writerow([
                mercadoria.codigo_rastreio,
                data_bipagem,
                hora_bipagem,
                transportadora,
                status
            ])
        
        # Preparar arquivo para download
        output.seek(0)
        
        # Criar arquivo temporário
        filename = f"conferencia_nestle_{datetime.now().strftime('%Y%m%d')}_{transportadora.replace(' ', '_')}.csv"
        
        # Retornar arquivo CSV
        csv_data = output.getvalue()
        output.close()
        
        # Criar resposta com arquivo
        from io import BytesIO
        buffer = BytesIO()
        buffer.write(csv_data.encode('utf-8-sig'))  # UTF-8 com BOM para Excel
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'erro': f'Erro ao exportar dados: {str(e)}'}), 500

@conferencia_bp.route("/transportadora/atualizar", methods=["POST"])
def atualizar_transportadora():
    """Atualiza a transportadora de uma mercadoria específica"""
    try:
        data = request.get_json()
        if not data or 'codigo_rastreio' not in data or 'transportadora' not in data:
            return jsonify({'erro': 'Código de rastreio e transportadora são obrigatórios'}), 400
        
        codigo = data['codigo_rastreio'].strip().upper()
        transportadora = data['transportadora'].strip()
        
        if not codigo or not transportadora:
            return jsonify({'erro': 'Código de rastreio e transportadora não podem estar vazios'}), 400
        
        # Buscar mercadoria
        mercadoria = MercadoriaConferida.query.filter_by(codigo_rastreio=codigo).first()
        
        if not mercadoria:
            return jsonify({'erro': 'Mercadoria não encontrada'}), 404
        
        # Atualizar transportadora
        mercadoria.transportadora = transportadora
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Transportadora atualizada para {transportadora}',
            'codigo': codigo,
            'transportadora': transportadora
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao atualizar transportadora: {str(e)}'}), 500

@conferencia_bp.route("/transportadora/atualizar-lote", methods=["POST"])
def atualizar_transportadora_lote():
    """Atualiza a transportadora de múltiplas mercadorias de uma vez - APENAS as que estão na base"""
    try:
        data = request.get_json()
        if not data or 'transportadora' not in data:
            return jsonify({'erro': 'Transportadora é obrigatória'}), 400
        
        transportadora = data['transportadora'].strip()
        if not transportadora:
            return jsonify({'erro': 'Transportadora não pode estar vazia'}), 400
        
        # Buscar mercadorias que não têm transportadora definida
        mercadorias_sem_transportadora = MercadoriaConferida.query.filter(
            (MercadoriaConferida.transportadora.is_(None)) | 
            (MercadoriaConferida.transportadora == '') |
            (MercadoriaConferida.transportadora == 'Não definida')
        ).all()
        
        # Filtrar APENAS as que estão na base
        mercadorias_na_base = []
        for mercadoria in mercadorias_sem_transportadora:
            rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=mercadoria.codigo_rastreio).first()
            if rastreio:  # SÓ incluir se estiver na base
                mercadorias_na_base.append(mercadoria)
        
        if not mercadorias_na_base:
            return jsonify({
                'mensagem': 'Todas as mercadorias na base já têm transportadora definida',
                'atualizadas': 0,
                'total_mercadorias': len(mercadorias_sem_transportadora),
                'mercadorias_na_base': len(mercadorias_na_base)
            })
        
        # Atualizar transportadora para todas as que estão na base
        for mercadoria in mercadorias_na_base:
            mercadoria.transportadora = transportadora
        
        db.session.commit()
        
        # Atualizar dashboard após mudança de transportadora
        try:
            hoje = datetime.now().date()
            recalcular_transportadoras_dashboard(hoje)
        except Exception as dashboard_error:
            print(f"Erro ao atualizar dashboard após mudança de transportadora: {dashboard_error}")
        
        return jsonify({
            'mensagem': f'Transportadora atualizada para {len(mercadorias_na_base)} mercadorias na base',
            'atualizadas': len(mercadorias_na_base),
            'total_mercadorias_sem_transportadora': len(mercadorias_sem_transportadora),
            'mercadorias_na_base_atualizadas': len(mercadorias_na_base),
            'transportadora': transportadora
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao atualizar transportadoras em lote: {str(e)}'}), 500

@conferencia_bp.route("/rastreios/excluir", methods=["DELETE"])
def excluir_rastreio():
    """Exclui um rastreio da base de rastreios esperados"""
    try:
        data = request.get_json()
        if not data or 'codigo_rastreio' not in data:
            return jsonify({'erro': 'Código de rastreio é obrigatório'}), 400
        
        codigo = data['codigo_rastreio'].strip().upper()
        if not codigo:
            return jsonify({'erro': 'Código de rastreio não pode estar vazio'}), 400
        
        # Buscar rastreio na base
        rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=codigo).first()
        
        if not rastreio:
            return jsonify({'erro': 'Rastreio não encontrado na base'}), 404
        
        # Excluir o rastreio
        db.session.delete(rastreio)
        db.session.commit()
        
        return jsonify({
            'mensagem': f'Rastreio {codigo} excluído com sucesso da base',
            'codigo': codigo
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao excluir rastreio: {str(e)}'}), 500

@conferencia_bp.route("/mercadorias/excluir", methods=["DELETE"])
def excluir_mercadoria():
    """Exclui uma mercadoria conferida da base"""
    try:
        data = request.get_json()
        if not data or 'codigo_rastreio' not in data:
            return jsonify({'erro': 'Código de rastreio é obrigatório'}), 400
        
        codigo = data['codigo_rastreio'].strip().upper()
        if not codigo:
            return jsonify({'erro': 'Código de rastreio não pode estar vazio'}), 400
        
        # Buscar mercadoria conferida
        mercadoria = MercadoriaConferida.query.filter_by(codigo_rastreio=codigo).first()
        
        if not mercadoria:
            return jsonify({'erro': 'Mercadoria não encontrada'}), 404
        
        # Verificar transportadora e status antes de excluir
        transportadora = mercadoria.transportadora or 'Não definida'
        status = 'sem_status'  # Por padrão
        
        # Verificar se está na base para determinar o status
        rastreio = RastreioEsperado.query.filter_by(codigo_rastreio=codigo).first()
        if rastreio:
            if rastreio.status == 'coleta':
                status = 'coleta'
            elif rastreio.status == 'insucesso':
                status = 'insucesso'
        
        # Excluir a mercadoria
        db.session.delete(mercadoria)
        db.session.commit()
        
        # Decrementar dashboard após exclusão
        try:
            hoje = datetime.now().date()
            cache = DashboardCache.query.filter_by(data=hoje).first()
            
            if cache:
                # Decrementar contadores
                if cache.total_hoje > 0:
                    cache.total_hoje -= 1
                
                if transportadora in cache.transportadoras and cache.transportadoras[transportadora] > 0:
                    cache.transportadoras[transportadora] -= 1
                
                if status == 'coleta' and cache.coleta_hoje > 0:
                    cache.coleta_hoje -= 1
                elif status == 'insucesso' and cache.insucesso_hoje > 0:
                    cache.insucesso_hoje -= 1
                elif cache.sem_status_hoje > 0:
                    cache.sem_status_hoje -= 1
                
                # Remover da lista de rastreios contados
                if cache.rastreios_contados:
                    rastreios_contados = json.loads(cache.rastreios_contados)
                    if codigo in rastreios_contados:
                        rastreios_contados.remove(codigo)
                        cache.rastreios_contados = json.dumps(rastreios_contados)
                
                cache.ultima_atualizacao = datetime.now()
                db.session.commit()
                
        except Exception as dashboard_error:
            # Se houver erro no dashboard, não afetar a exclusão
            print(f"Erro ao decrementar dashboard após exclusão: {dashboard_error}")
        
        return jsonify({
            'mensagem': f'Mercadoria {codigo} excluída com sucesso',
            'codigo': codigo
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro ao excluir mercadoria: {str(e)}'}), 500

