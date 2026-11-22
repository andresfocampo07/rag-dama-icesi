---
id_doc: A2_07
titulo: "Data Integration and Interoperability - DAMA-DMBOK2 context diagram"
area_dama: Integración e interoperabilidad de datos
capa: A
autoridad: primaria
fuente: "DAMA International, DAMA-DMBOK2 Revised Edition, context diagram (https://dama.org/dmbok)"
licencia: "CC BY-ND 4.0 - transcripción literal, sin modificaciones ni traducción"
idioma: en
imagen: A2_07_integracion.png
---

# Integración e interoperabilidad de datos (Data Integration and Interoperability)

Transcripción literal del diagrama de contexto oficial de DAMA-DMBOK2. © DAMA International, CC BY-ND 4.0.

## Definition
Managing the movement and consolidation of data within and between applications and organizations. Data Interoperability is the ability for multiple systems to communicate.

## Goals
1. Make data available from disparate sources in the format and timeframe needed.
2. Lower cost and complexity of managing solutions by developing shared models and interfaces.
3. Identify meaningful events and automatically trigger alerts and actions.
4. Support business intelligence, analytics, master data management, and operational efficiency efforts.

## Business drivers

### Inputs
- Business Goals & Strategies
- Data Needs & Standards
- Regulatory, Compliance, & Security Requirements
- Data, Process, Application, and Technical Architectures
- Data Semantics
- Source Data

### Activities
1. Plan & Analyze (P)
   1. Define data integration and lifecycle requirements
   2. Perform Data Discovery
   3. Document Data Lineage
   4. Profile Data
   5. Examine Business Rule Compliance
2. Design DII Solutions (P)
   1. Design DII Architecture
   2. Model Data Hubs, Interfaces, Messages, and Data Services
   3. Map Sources to Targets
   4. Design Data Orchestration
3. Develop DII Solutions (D)
   1. Develop Data Services
   2. Develop Data Flow
   3. Develop Data Migration Approach
   4. Develop a Publication Approach
   5. Develop Complex Event Processing Flows
4. Implement and Monitor (O)
   1. Maintain DII Metadata

### Deliverables
- DII Architecture
- Data Exchange Specifications
- Data Access Agreements
- Data Services
- Complex Event Processing Thresholds and Alerts

### Suppliers
- Data Producers
- Architecture Board
- IT Steering Committee
- Executives and Managers
- Subject Matter Experts

### Participants
- Data Architects
- Business and Data Analysts
- Data Modelers
- DII Developers
- Project and Program Managers
- Data Stewards

### Consumers
- Customers, Partners
- Information Consumers
- Knowledge Workers
- Managers and Executives

## Technical drivers

### Techniques
- Loosely coupled applications
- Minimize the number of interfaces
- Create standard canonical interfaces
- Service Orchestration

### Tools
- Data Transformation Engine
- Business Rules Engine
- Data Virtualization Server
- Enterprise Service Bus
- Data and Process Modeling Tools
- Data Profiling Tool
- Metadata Repository

### Metrics
- Data Availability
- Data Volumes and Speed
- Solution Costs and Complexity

Note: DII = Data Integration and Interoperability.

Legend: (P) Planning, (C) Control, (D) Development, (O) Operations
