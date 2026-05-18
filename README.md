# Gerenciamento de Dados Pessoais

Nesse projeto, eu construo uma infraestrutura de dados Prefect + DBT 
para organizar meus dados pessoais e gerar insights sobre comportamentos e práticas.

## Build

```bash
prefect server start

prefect deploy

prefect worker start --pool "process_pool_0"
```
