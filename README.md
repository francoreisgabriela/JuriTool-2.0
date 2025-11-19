# 📘 **JuriToolbox — Caixa de Ferramentas Jurídicas (Educacional)**

O **JuriToolbox** é um aplicativo interativo desenvolvido em **Python + Streamlit** que reúne três ferramentas jurídicas essenciais para estudo: cálculo de prazos, verificação de elegibilidade ao ANPP e uma simulação didática da dosimetria da pena.

> 🚨 **Aviso legal importante:**  
> Este projeto tem **finalidade exclusivamente educacional**.  
> Ele **não substitui consulta jurídica**, não deve ser usado em casos reais e contém **regras simplificadas** em relação às normas e práticas forenses.

---

# ⚖️ Funcionalidades do JuriToolbox

## 🔹 1. **Calculadora de Prazos Processuais (CPC/CPP)**

Ferramenta para contar prazos em:
- **Dias corridos**
- **Dias úteis** (excluindo sábados, domingos e feriados enviados por CSV)

Recursos:
- Upload de CSV com feriados (coluna `data`)
- Linha do tempo completa do prazo
- Cálculo simplificado: exclui o dia do começo e inicia a contagem no dia seguinte

---

## 🔹 2. **Elegibilidade ao ANPP (art. 28-A do CPP)**

Checklist guiado para avaliar, de forma **didática**, se um caso é *potencialmente elegível* ao Acordo de Não Persecução Penal.

Critérios avaliados:
- Ausência de violência ou grave ameaça  
- Pena mínima inferior a 4 anos  
- Confissão formal  
- Reincidência dolosa  
- Violência doméstica e de gênero  
- Benefício prévio de ANPP  

Recursos:
- Parecer automático em linguagem natural
- Consulta ao artigo do CP usando o CSV (`cp.csv`)

---

## 🔹 3. **Dosimetria Simplificada (art. 59 do CP)**

Simulação numérica da fixação da pena:

**1ª fase – Pena-base**
- Avaliação das 8 circunstâncias judiciais (culpabilidade, antecedentes, motivos etc.)
- Sistema de ajuste numérico simplificado (favorável, neutra, desfavorável)

**2ª e 3ª fases – Causas de aumento/diminuição**
- Possibilidade de inserir causas com percentuais  
- Cálculo sequencial da pena final  
- Conversão aproximada em anos e meses

**Extra:**  
Geração de **rascunho de fundamentação jurídica**, ideal para estudo.

---

# 📁 Estrutura do Projeto

```text
JuriToolbox/
│
├── app.py          # Aplicativo Streamlit principal
├── cp.csv          # Código Penal (em CSV)
├── cpp.csv         # Código de Processo Penal (em CSV)
└── README.md       # Este arquivo
