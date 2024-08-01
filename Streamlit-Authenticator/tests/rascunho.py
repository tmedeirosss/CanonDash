 # Resto do código para manipulação e visualização dos dados
            A4Pb = 0
            A4Cor = 0
            A3Pb = 0
            A3cor = 0
            
            informacoes = {
                'Categorias': ['A4Pb', 'A4Cor', 'A3Pb', 'A3cor'],
                'Valores': [A4Pb, A4Cor, A3Pb, A3cor]
            }

            fig = px.bar(data, y='start_101', x='SerialNumber', title='Total por Equipamento')
            st.plotly_chart(fig)

            data['data'] = pd.to_datetime(data['data'])
            data['start_101'] = pd.to_numeric(data['start_101'], errors='coerce')
            data['end_101'] = pd.to_numeric(data['end_101'], errors='coerce')
            
            data_grouped = data.groupby('data').agg({'start_101': 'sum', 'end_101': 'sum'}).reset_index()
            data_grouped['production'] = data_grouped['end_101'] - data_grouped['start_101']

            ig = px.line(data_grouped, x='data', y='production', title='Produção ao Longo do Tempo')
            st.plotly_chart(ig)

            data_unique = data.drop_duplicates(subset=['SerialNumber'])
            selected_serial = st.selectbox('Selecione um equipamento para detalhes', data_unique['SerialNumber'])

            equipamento_data = data[data['SerialNumber'] == selected_serial]
            a4pbserie = equipamento_data.start_113.replace(0, pd.NA).mean()
            equipamento_data.start_112.fillna(0, inplace=True)
            a3pbserie = equipamento_data.start_112.astype(int).mean().astype(int)
            a4corserie = (equipamento_data.start_230 + equipamento_data.start_322) - equipamento_data.start_113
            a3corserie = (equipamento_data.start_229 + equipamento_data.start_321) - equipamento_data.start_112.astype(float).astype(int)
            a3corserie.fillna(0, inplace=True)
            a3corserie = a3corserie.mean().astype(int)
            a3corserie = a3corserie if a3corserie > 0 else 0

            cores = ['#1f77b4', '#ff7f0e']
            col1, col2 = st.columns(2)

            with col1:
                pz1 = px.pie(names=('P&B', 'COR'), values=[a4pbserie, (a4corserie.mean() if a4corserie.mean() > 0 else 0)], title='Impressões A4', color_discrete_sequence=cores)
                st.plotly_chart(pz1)

            with col2:
                pz2 = px.pie(names=('P&B', 'COR'), values=[a3pbserie, a3corserie], title='Impressões A3', color_discrete_sequence=cores)
                st.plotly_chart(pz2)
        else:
            st.error("Nenhum dado foi retornado.")
    else:
        st.error("Por favor, digite um ID válido.")




if st.sidebar.button("Salvar Código do Cliente"):
                client_code_input = decrypt_code(client_code_input)
                # Atualizar a configuração do cliente
                config['credentials']['usernames'][client_id]['client_code'] = int(client_code_input)