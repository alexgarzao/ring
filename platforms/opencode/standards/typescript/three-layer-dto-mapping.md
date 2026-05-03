## Three-Layer DTO Mapping (MANDATORY)

**HARD GATE:** All data transformations MUST use three-layer DTO mapping. Direct object passing between layers is FORBIDDEN.

### The Three Layers

```
┌──────────────────────────────────────────────────────────────┐
│  HTTP Layer (Controllers)                                     │
│  └── HTTP DTOs (CreateOrganizationDto, OrganizationResponse) │
├──────────────────────────────────────────────────────────────┤
│  Domain Layer (Use Cases)                                     │
│  └── Domain Entities (Organization)                           │
├──────────────────────────────────────────────────────────────┤
│  Infrastructure Layer (External Services)                     │
│  └── External DTOs (Core oneOrganizationDto)                    │
└──────────────────────────────────────────────────────────────┘
```

### Mapper Interfaces

```typescript
// Domain ↔ HTTP Mapper
interface EntityMapper<Entity, HttpDto, CreateDto> {
    toEntity(dto: HttpDto): Entity;
    toDto(entity: Entity): HttpDto;
    fromCreateDto(dto: CreateDto): Partial<Entity>;
}

// Domain ↔ External Service Mapper
interface ExternalMapper<Entity, ExternalDto> {
    toDomain(external: ExternalDto): Entity;
    toExternal(entity: Entity): ExternalDto;
}
```

### Implementation Example

```typescript
// src/core/domain/entities/organization.ts
export interface Organization {
    id: string;
    name: string;
    status: OrganizationStatus;
    createdAt: Date;
    updatedAt: Date;
}

// src/core/infrastructure/http/dto/organization.dto.ts (HTTP Layer)
export interface CreateOrganizationDto {
    name: string;
}

export interface OrganizationResponseDto {
    id: string;
    name: string;
    status: string;
    created_at: string;  // snake_case for API response
    updated_at: string;
}

// src/core/infrastructure/http/dto/midaz-organization.dto.ts (External Service)
export interface Core oneOrganizationDto {
    organization_id: string;
    organization_name: string;
    org_status: string;
    created_timestamp: string;
}

// src/core/infrastructure/http/mappers/organization.mapper.ts
export class OrganizationMapper implements EntityMapper<Organization, OrganizationResponseDto, CreateOrganizationDto> {
    toEntity(dto: OrganizationResponseDto): Organization {
        return {
            id: dto.id,
            name: dto.name,
            status: dto.status as OrganizationStatus,
            createdAt: new Date(dto.created_at),
            updatedAt: new Date(dto.updated_at),
        };
    }

    toDto(entity: Organization): OrganizationResponseDto {
        return {
            id: entity.id,
            name: entity.name,
            status: entity.status,
            created_at: entity.createdAt.toISOString(),
            updated_at: entity.updatedAt.toISOString(),
        };
    }

    fromCreateDto(dto: CreateOrganizationDto): Partial<Organization> {
        return {
            name: dto.name,
            status: 'active' as OrganizationStatus,
        };
    }
}

// src/core/infrastructure/http/mappers/midaz-organization.mapper.ts
export class Core oneOrganizationMapper implements ExternalMapper<Organization, Core oneOrganizationDto> {
    toDomain(external: Core oneOrganizationDto): Organization {
        return {
            id: external.organization_id,
            name: external.organization_name,
            status: this.mapStatus(external.org_status),
            createdAt: new Date(external.created_timestamp),
            updatedAt: new Date(), // External doesn't provide this
        };
    }

    toExternal(entity: Organization): Core oneOrganizationDto {
        return {
            organization_id: entity.id,
            organization_name: entity.name,
            org_status: entity.status.toUpperCase(),
            created_timestamp: entity.createdAt.toISOString(),
        };
    }

    private mapStatus(externalStatus: string): OrganizationStatus {
        const statusMap: Record<string, OrganizationStatus> = {
            'ACTIVE': 'active',
            'INACTIVE': 'inactive',
            'SUSPENDED': 'suspended',
        };
        return statusMap[externalStatus] ?? 'inactive';
    }
}
```

### Data Flow

```
Client Request
    │
    ▼
[HTTP DTO] ──────────────────────────────────────────────┐
    │                                                     │
    │ OrganizationMapper.fromCreateDto()                 │
    ▼                                                     │
[Domain Entity] ←─────────────────────────────────────────┤
    │                                                     │
    │ Core oneOrganizationMapper.toExternal()               │
    ▼                                                     │
[External DTO] → External Service                        │
    │                                                     │
    │ Core oneOrganizationMapper.toDomain()                 │
    ▼                                                     │
[Domain Entity] ──────────────────────────────────────────┤
    │                                                     │
    │ OrganizationMapper.toDto()                         │
    ▼                                                     │
[HTTP DTO] → Client Response                              │
```

### Anti-Rationalization Table

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Same shape, no mapper needed" | Shapes evolve independently. Today same, tomorrow different. | **Create mapper now. Decouple layers.** |
| "Too much boilerplate" | Boilerplate < debugging type mismatches in production. | **Write the mapper. It's documentation.** |
| "External service uses same format" | External services change without notice. Mapper isolates impact. | **Always map. Never trust external shapes.** |
| "Just pass-through for now" | Tech debt. Every pass-through becomes a bug later. | **Map from day one.** |

---

