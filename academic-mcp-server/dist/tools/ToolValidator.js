"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ToolValidator = void 0;
class ToolValidator {
    static validateRegistration(registration) {
        const errors = [];
        const warnings = [];
        const metadataResult = this.validateMetadata(registration.metadata);
        errors.push(...metadataResult.errors);
        warnings.push(...(metadataResult.warnings || []));
        if (typeof registration.handler !== 'function') {
            errors.push('Tool handler must be a function');
        }
        if (registration.permissions) {
            if (!Array.isArray(registration.permissions)) {
                errors.push('Tool permissions must be an array');
            }
            else {
                registration.permissions.forEach((permission, index) => {
                    if (typeof permission !== 'string' || permission.trim().length === 0) {
                        errors.push(`Permission at index ${index} must be a non-empty string`);
                    }
                });
            }
        }
        if (registration.rateLimit) {
            const { requests, windowMs } = registration.rateLimit;
            if (typeof requests !== 'number' || requests <= 0) {
                errors.push('Rate limit requests must be a positive number');
            }
            if (typeof windowMs !== 'number' || windowMs <= 0) {
                errors.push('Rate limit windowMs must be a positive number');
            }
        }
        return {
            valid: errors.length === 0,
            errors,
            warnings: warnings.length > 0 ? warnings : undefined,
        };
    }
    static validateMetadata(metadata) {
        const errors = [];
        const warnings = [];
        if (!metadata.name || typeof metadata.name !== 'string') {
            errors.push('Tool name is required and must be a string');
        }
        else {
            if (!/^[a-zA-Z][a-zA-Z0-9_-]*$/.test(metadata.name)) {
                errors.push('Tool name must start with a letter and contain only letters, numbers, underscores, and hyphens');
            }
            if (metadata.name.length > 64) {
                errors.push('Tool name must not exceed 64 characters');
            }
        }
        if (!metadata.description || typeof metadata.description !== 'string') {
            errors.push('Tool description is required and must be a string');
        }
        else if (metadata.description.length > 500) {
            errors.push('Tool description must not exceed 500 characters');
        }
        if (!metadata.version || typeof metadata.version !== 'string') {
            errors.push('Tool version is required and must be a string');
        }
        else if (!/^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$/.test(metadata.version)) {
            warnings.push('Tool version should follow semantic versioning (e.g., 1.0.0)');
        }
        if (metadata.category && typeof metadata.category !== 'string') {
            errors.push('Tool category must be a string');
        }
        if (metadata.tags) {
            if (!Array.isArray(metadata.tags)) {
                errors.push('Tool tags must be an array');
            }
            else {
                metadata.tags.forEach((tag, index) => {
                    if (typeof tag !== 'string' || tag.trim().length === 0) {
                        errors.push(`Tag at index ${index} must be a non-empty string`);
                    }
                });
            }
        }
        if (metadata.deprecated !== undefined && typeof metadata.deprecated !== 'boolean') {
            errors.push('Tool deprecated flag must be a boolean');
        }
        if (metadata.experimental !== undefined && typeof metadata.experimental !== 'boolean') {
            errors.push('Tool experimental flag must be a boolean');
        }
        const schemaResult = this.validateParameterSchema(metadata.inputSchema);
        errors.push(...schemaResult.errors);
        warnings.push(...(schemaResult.warnings || []));
        return {
            valid: errors.length === 0,
            errors,
            warnings: warnings.length > 0 ? warnings : undefined,
        };
    }
    static validateParameterSchema(schema) {
        const errors = [];
        const warnings = [];
        if (!schema || typeof schema !== 'object') {
            errors.push('Schema must be a valid object');
            return { valid: false, errors };
        }
        if (!schema.type) {
            errors.push('Schema must have a type field');
            return { valid: false, errors };
        }
        const validTypes = ['object', 'array', 'string', 'number', 'boolean', 'null'];
        if (!validTypes.includes(schema.type)) {
            errors.push(`Invalid schema type: ${schema.type}. Must be one of: ${validTypes.join(', ')}`);
            return { valid: false, errors };
        }
        if (schema.type === 'object') {
            if (schema.properties) {
                if (typeof schema.properties !== 'object' || schema.properties === null) {
                    errors.push('Object schema properties must be an object');
                }
                else {
                    for (const [propName, propSchema] of Object.entries(schema.properties)) {
                        if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(propName)) {
                            warnings.push(`Property name '${propName}' should start with a letter and contain only letters, numbers, and underscores`);
                        }
                        const propResult = this.validateParameterSchema(propSchema);
                        errors.push(...propResult.errors.map(err => `Property '${propName}': ${err}`));
                        warnings.push(...(propResult.warnings || []).map(warn => `Property '${propName}': ${warn}`));
                    }
                }
            }
            if (schema.required) {
                if (!Array.isArray(schema.required)) {
                    errors.push('Object schema required must be an array');
                }
                else {
                    schema.required.forEach((req, index) => {
                        if (typeof req !== 'string') {
                            errors.push(`Required property at index ${index} must be a string`);
                        }
                        else if (schema.properties && !schema.properties[req]) {
                            errors.push(`Required property '${req}' is not defined in properties`);
                        }
                    });
                }
            }
        }
        if (schema.type === 'array') {
            if (schema.items) {
                const itemsResult = this.validateParameterSchema(schema.items);
                errors.push(...itemsResult.errors.map(err => `Array items: ${err}`));
                warnings.push(...(itemsResult.warnings || []).map(warn => `Array items: ${warn}`));
            }
        }
        if (schema.type === 'string') {
            if (schema.minLength !== undefined) {
                if (typeof schema.minLength !== 'number' || schema.minLength < 0) {
                    errors.push('String minLength must be a non-negative number');
                }
            }
            if (schema.maxLength !== undefined) {
                if (typeof schema.maxLength !== 'number' || schema.maxLength < 0) {
                    errors.push('String maxLength must be a non-negative number');
                }
            }
            if (schema.minLength !== undefined && schema.maxLength !== undefined && schema.minLength > schema.maxLength) {
                errors.push('String minLength cannot be greater than maxLength');
            }
            if (schema.pattern !== undefined && typeof schema.pattern !== 'string') {
                errors.push('String pattern must be a string');
            }
        }
        if (schema.type === 'number') {
            if (schema.minimum !== undefined && typeof schema.minimum !== 'number') {
                errors.push('Number minimum must be a number');
            }
            if (schema.maximum !== undefined && typeof schema.maximum !== 'number') {
                errors.push('Number maximum must be a number');
            }
            if (schema.minimum !== undefined && schema.maximum !== undefined && schema.minimum > schema.maximum) {
                errors.push('Number minimum cannot be greater than maximum');
            }
        }
        if (schema.enum !== undefined) {
            if (!Array.isArray(schema.enum) || schema.enum.length === 0) {
                errors.push('Schema enum must be a non-empty array');
            }
        }
        return {
            valid: errors.length === 0,
            errors,
            warnings: warnings.length > 0 ? warnings : undefined,
        };
    }
    static validateArguments(args, schema) {
        const errors = [];
        if (schema.type === 'object') {
            if (schema.required) {
                for (const requiredProp of schema.required) {
                    if (!(requiredProp in args)) {
                        errors.push(`Required property '${requiredProp}' is missing`);
                    }
                }
            }
            if (schema.properties) {
                for (const [propName, value] of Object.entries(args)) {
                    const propSchema = schema.properties[propName];
                    if (!propSchema) {
                        errors.push(`Unknown property '${propName}'`);
                    }
                    else {
                        const propResult = this.validateValue(value, propSchema, propName);
                        errors.push(...propResult.errors);
                    }
                }
            }
        }
        return {
            valid: errors.length === 0,
            errors,
        };
    }
    static validateValue(value, schema, path) {
        const errors = [];
        if (!this.validateType(value, schema.type)) {
            errors.push(`${path}: Expected ${schema.type}, got ${typeof value}`);
            return { valid: false, errors };
        }
        if (schema.enum && !schema.enum.includes(value)) {
            errors.push(`${path}: Value must be one of: ${schema.enum.join(', ')}`);
        }
        if (schema.type === 'string' && typeof value === 'string') {
            if (schema.minLength !== undefined && value.length < schema.minLength) {
                errors.push(`${path}: String must be at least ${schema.minLength} characters`);
            }
            if (schema.maxLength !== undefined && value.length > schema.maxLength) {
                errors.push(`${path}: String must not exceed ${schema.maxLength} characters`);
            }
            if (schema.pattern && !new RegExp(schema.pattern).test(value)) {
                errors.push(`${path}: String does not match required pattern`);
            }
        }
        if (schema.type === 'number' && typeof value === 'number') {
            if (schema.minimum !== undefined && value < schema.minimum) {
                errors.push(`${path}: Number must be at least ${schema.minimum}`);
            }
            if (schema.maximum !== undefined && value > schema.maximum) {
                errors.push(`${path}: Number must not exceed ${schema.maximum}`);
            }
        }
        return {
            valid: errors.length === 0,
            errors,
        };
    }
    static validateType(value, expectedType) {
        switch (expectedType) {
            case 'string':
                return typeof value === 'string';
            case 'number':
                return typeof value === 'number' && !isNaN(value);
            case 'boolean':
                return typeof value === 'boolean';
            case 'object':
                return typeof value === 'object' && value !== null && !Array.isArray(value);
            case 'array':
                return Array.isArray(value);
            case 'null':
                return value === null;
            default:
                return false;
        }
    }
}
exports.ToolValidator = ToolValidator;
//# sourceMappingURL=ToolValidator.js.map