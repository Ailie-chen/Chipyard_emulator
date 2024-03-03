int main() {
    int *a = (int *)malloc(sizeof(int)); // 动态分配内存
    *a = 10;                             // 这里的赋值操作将会在编译后的汇编代码中产生store指令
    int *b = (int *)malloc(sizeof(int)); // 再次动态分配内存
    *b = *a;                             // 这个赋值操作将会在编译后的汇编代码中产生load指令
    printf("*b = %d\n", *b);
    free(a);                             // 释放分配的内存
    free(b);                             // 释放分配的内存
    return 0;
}