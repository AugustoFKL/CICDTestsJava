package org.example;

import uniffi.cicd_ffi.CreateSchema;
import uniffi.cicd_ffi.SchemaName;

// Press Shift twice to open the Search Everywhere dialog and type `show whitespaces`,
// then press Enter. You can now see whitespace characters in your code.
public class Main {
    public static void main(String[] args) {

        final SchemaName schemaName = new SchemaName.Name("test");
        final CreateSchema createSchema = new CreateSchema(true, schemaName);
        System.out.printf("%s", createSchema.schemaName().toString());
    }
}
