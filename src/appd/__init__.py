"""Funções auxiliares do Trabalho Final APPD (Programa Academia da Saúde).

Módulos:
- download: acesso às fontes originais (DATASUS via PySUS, IBGE via API e SIDRA).
- agregacao: classificação de CID, agregação de SIH/CNES e chaves de município.
- estimacao: balanceamento (SMD), bootstrap, tabela-síntese e MDE.
"""

SEMENTE = 42
