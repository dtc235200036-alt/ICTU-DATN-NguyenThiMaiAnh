## 1.9. Kết luận chương

> **Mã PI:** — — **Yêu cầu:** —

Chương này đã trình bày cơ sở lý thuyết của toàn bộ công nghệ chính được sử dụng để hiện thực hóa hệ thống: nguyên lý kiến trúc hướng dịch vụ (SOA), RESTful API, xác thực JWT và kiểm soát truy cập theo vai trò (RBAC) làm nền tảng cho việc tách hệ thống thành ba thành phần độc lập với ranh giới rõ ràng; Python, FastAPI, Pydantic, SQLAlchemy 2.0 và Alembic làm nền tảng xây dựng Web API và Dịch vụ AI; MySQL 8 với bảng mã `utf8mb4`, collation `utf8mb4_vietnamese_ci` và chuẩn hóa Unicode NFC để lưu trữ và so sánh chính xác dữ liệu tiếng Việt; React, TypeScript, Vite, Ant Design và TanStack Query làm nền tảng client Web; Apache, HTTPS/TLS và Docker Compose làm hạ tầng triển khai đáp ứng yêu cầu bảo mật và phân quyền của đề cương; và cuối cùng, nhóm công nghệ trung tâm của tính năng AI — tách từ tiếng Việt, mô hình embedding câu theo kiến trúc bi-encoder (PhoBERT hoặc E5 đa ngôn ngữ), tìm kiếm vector bằng FAISS, phát hiện sao chép nguyên văn bằng vân tay k-gram (winnowing) kèm lọc cụm phổ biến, và quy trình hiệu chỉnh ngưỡng thực nghiệm — làm nền tảng cho tính năng kiểm tra trùng lặp tên đề tài và nội dung đề cương/báo cáo, được xác định rõ là bổ sung chứ không thay thế công cụ kiểm duyệt chống đạo văn chính thức của trường (Turnitin). Các khái niệm và quyết định công nghệ trình bày ở đây là cơ sở tham chiếu trực tiếp cho nội dung khảo sát/phân tích ở Chương 2, thiết kế chi tiết (kiến trúc, CSDL, giao diện) ở Chương 3, và trình bày kết quả triển khai/thử nghiệm ở Chương 4.

### Tài liệu tham khảo

1. Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures* (Chapter 5 — Representational State Transfer, REST). Doctoral dissertation, University of California, Irvine.
2. IETF. *RFC 7519 — JSON Web Token (JWT)*. https://www.rfc-editor.org/rfc/rfc7519 (truy cập 09/2026).
3. FastAPI — Official Documentation. https://fastapi.tiangolo.com/ (truy cập 09/2026).
4. Pydantic — Official Documentation. https://docs.pydantic.dev/ (truy cập 09/2026).
5. SQLAlchemy 2.0 — Official Documentation. https://docs.sqlalchemy.org/en/20/ (truy cập 09/2026).
6. Alembic — Official Documentation. https://alembic.sqlalchemy.org/ (truy cập 09/2026).
7. PyJWT — Official Documentation. https://pyjwt.readthedocs.io/ (truy cập 09/2026).
8. MySQL 8.0 Reference Manual — *The utf8mb4 Character Set (4-Byte UTF-8 Unicode Encoding)*. https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html (truy cập 09/2026).
9. Unicode Consortium. *Unicode Standard Annex #15 — Unicode Normalization Forms* (định nghĩa NFC/NFD). https://unicode.org/reports/tr15/ (truy cập 09/2026).
10. React — Official Documentation. https://react.dev/ (truy cập 09/2026).
11. Vite — Official Documentation. https://vite.dev/ (truy cập 09/2026).
12. Ant Design — Official Documentation. https://ant.design/ (truy cập 09/2026).
13. TanStack Query — Official Documentation. https://tanstack.com/query/latest (truy cập 09/2026).
14. Apache HTTP Server — *mod_proxy Documentation*. https://httpd.apache.org/docs/current/mod/mod_proxy.html (truy cập 09/2026).
15. Docker — *Docker Compose Overview*. https://docs.docker.com/compose/ (truy cập 09/2026).
16. underthesea — Vietnamese NLP Toolkit. https://github.com/undertheseanlp/underthesea (truy cập 09/2026).
17. Nguyen, D. Q., & Nguyen, A. T. (2020). *PhoBERT: Pre-trained language models for Vietnamese*. Findings of the Association for Computational Linguistics: EMNLP 2020, pp. 1037–1042. https://arxiv.org/abs/2003.00744 (truy cập 09/2026).
18. Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP-IJCNLP), pp. 3982–3992. https://arxiv.org/abs/1908.10084 (truy cập 09/2026).
19. bkai-foundation-models. *vietnamese-bi-encoder* (model card, Hugging Face). https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder (truy cập 09/2026).
20. Wang, L., Yang, N., Huang, X., Jiao, B., Yang, L., Jiang, D., Majumder, R., & Wei, F. (2022). *Text Embeddings by Weakly-Supervised Contrastive Pre-training*. arXiv:2212.03533. https://arxiv.org/abs/2212.03533 (truy cập 09/2026).
21. Johnson, J., Douze, M., & Jégou, H. (2019). *Billion-scale similarity search with GPUs*. IEEE Transactions on Big Data. arXiv:1702.08734. https://arxiv.org/abs/1702.08734 (truy cập 09/2026).
22. Broder, A. Z. (1997). *On the resemblance and containment of documents*. Proceedings of Compression and Complexity of Sequences (SEQUENCES'97), IEEE, pp. 21–29. DOI: 10.1109/SEQUEN.1997.666900 (truy cập 09/2026).
23. Schleimer, S., Wilkerson, D. S., & Aiken, A. (2003). *Winnowing: Local Algorithms for Document Fingerprinting*. Proceedings of the 2003 ACM SIGMOD International Conference on Management of Data, pp. 76–85. DOI: 10.1145/872757.872770 (truy cập 10/2026).
24. Sorokina, D., Gehrke, J., Warner, S., & Ginsparg, P. (2006). *Plagiarism Detection in arXiv*. Proceedings of the Sixth International Conference on Data Mining (ICDM'06), IEEE. arXiv:cs/0702012. https://arxiv.org/abs/cs/0702012 (truy cập 10/2026).
25. Object Management Group (OMG). *Business Process Model and Notation (BPMN), Version 2.0*. https://www.omg.org/spec/BPMN/2.0/ (truy cập 09/2026).
26. Object Management Group (OMG). *Unified Modeling Language (UML)*. https://www.omg.org/spec/UML/ (truy cập 09/2026).
27. PlantUML — Official Documentation. https://plantuml.com/ (truy cập 09/2026).
28. draw.io (diagrams.net) — Official Documentation. https://www.drawio.com/ (truy cập 09/2026).
