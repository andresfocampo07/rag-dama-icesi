---
id_doc: A2_05
titulo: "Data Storage and Operations - DAMA-DMBOK2 context diagram"
area_dama: Almacenamiento y operaciones de datos
capa: A
autoridad: primaria
fuente: "DAMA International, DAMA-DMBOK2 Revised Edition, context diagram (https://dama.org/dmbok)"
licencia: "CC BY-ND 4.0 - transcripción literal, sin modificaciones ni traducción"
idioma: en
imagen: A2_05_almacenamiento.png
---

# Almacenamiento y operaciones de datos (Data Storage and Operations)

Transcripción literal del diagrama de contexto oficial de DAMA-DMBOK2. © DAMA International, CC BY-ND 4.0.

## Definition
The design, implementation, and support of stored data to maximize its value.

## Goals
1. Manage availability of data throughout the data lifecycle.
2. Ensure the integrity of data assets.
3. Manage performance of data transactions.

## Business drivers

### Inputs
- Data Architecture
- Data Requirements
- Data Models
- Service Level Agreements

### Activities
1. Manage Database Technology
   1. Understand Database Technology (P)
   2. Evaluate Database Technology (D)
   3. Manage and Monitor Database Technology (O)
2. Manage Database Operations
   1. Understand Requirements (P)
   2. Plan for Business Continuity (P)
   3. Develop Database Instances (D)
   4. Manage Database Performance (C,O)
   5. Manage Test Datasets (O)
   6. Manage Data Migration (O)

### Deliverables
- Database Technology Evaluation Criteria
- Database Environments
- Migrated/Replicated/Versioned Data
- Disaster Recovery Plan for Data in the Business Continuity Plans
- Database Operations Reports

### Suppliers
- Data Architect
- Data Modeler
- Software Developer
- Application Testing Team

### Participants
- Database Administrator
- Database Technology Specialist
- Data Modeler
- Data Architect

### Consumers
- Data Modeler
- Software Developer
- Application Testing Team
- Infrastructure Operations Team
- Executives and Managers

## Technical drivers

### Techniques
- Test in Lower Environments
- Physical Naming Standards
- Script Usage for All Changes

### Tools
- Data Modeling Tools
- Database Monitoring Tools
- Database Management Tools
- Developer Support Tools

### Metrics
- Data Storage Metrics
- Performance Metrics
- Operations Metrics
- Service Metrics

Legend: (P) Planning, (C) Control, (D) Development, (O) Operations
