import { ToolParameterSchema, ToolMetadata, ToolValidationResult, ToolRegistration } from './types';
export declare class ToolValidator {
    static validateRegistration(registration: ToolRegistration): ToolValidationResult;
    static validateMetadata(metadata: ToolMetadata): ToolValidationResult;
    static validateParameterSchema(schema: ToolParameterSchema): ToolValidationResult;
    static validateArguments(args: Record<string, unknown>, schema: ToolParameterSchema): ToolValidationResult;
    private static validateValue;
    private static validateType;
}
//# sourceMappingURL=ToolValidator.d.ts.map