from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings
import os
from .models import File
from .serializers import FileSerializer, FileUploadSerializer
from posts.models import Post # Import Post model to link files
import mimetypes

# Placeholder for AI moderation functions
def moderate_image(file_path):
    # Integrate with Google Vision API
    # Example: from google.cloud import vision
    # client = vision.ImageAnnotatorClient()
    # image = vision.Image(content=open(file_path, 'rb').read())
    # response = client.safe_search_detection(image=image)
    # safe_search = response.safe_search_annotation
    # return {"adult": safe_search.adult.name, "violence": safe_search.violence.name}
    return {"status": "ok", "reason": "Placeholder for image moderation"}

def moderate_pdf(file_path):
    # Integrate with PyPDF2 for text extraction and then AI moderation
    # Example:
    # import PyPDF2
    # reader = PyPDF2.PdfReader(file_path)
    # text = ""
    # for page in reader.pages:
    #     text += page.extract_text()
    # # Then send 'text' to a text-based AI moderation API (e.g., custom model, or Natural Language API)
    # return {"status": "ok", "extracted_text_len": len(text)}
    return {"status": "ok", "reason": "Placeholder for PDF moderation"}


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow anyone to view, only auth to upload/delete

    def create(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        post_id = serializer.validated_data.get('post_id')
        post = None
        if post_id:
            try:
                post = Post.objects.get(id=post_id)
            except Post.DoesNotExist:
                return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Save the file locally first
        file_instance = File(post=post, file=uploaded_file, size=uploaded_file.size)
        file_instance.file_type = uploaded_file.content_type
        file_instance.save() # This saves the file to MEDIA_ROOT

        # Trigger AI moderation
        file_path = file_instance.file.path
        moderation_result = {}
        if 'image' in file_instance.file_type:
            moderation_result = moderate_image(file_path)
        elif 'pdf' in file_instance.file_type:
            moderation_result = moderate_pdf(file_path)
        else:
            moderation_result = {"status": "skipped", "reason": "Unsupported file type for AI moderation."}

        file_instance.ai_moderation = moderation_result
        file_instance.save() # Update with moderation results

        headers = self.get_success_headers(serializer.data)
        return Response(FileSerializer(file_instance).data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, pk=None):
        file_instance = get_object_or_404(File, pk=pk)
        file_path = file_instance.file.path
        if not os.path.exists(file_path):
            return Response({'detail': 'File not found on server.'}, status=status.HTTP_404_NOT_FOUND)

        # Serve the file directly
        response = FileResponse(open(file_path, 'rb'), content_type=file_instance.file_type)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"' # or attachment
        return response

    def destroy(self, request, pk=None):
        file_instance = get_object_or_404(File, pk=pk)
        # Ensure only the author of the associated post (or admin) can delete the file
        if file_instance.post and file_instance.post.author != request.user and not request.user.is_staff:
            return Response({'detail': 'You do not have permission to delete this file.'}, status=status.HTTP_403_FORBIDDEN)

        # Delete the file from local storage
        file_path = file_instance.file.path
        if os.path.exists(file_path):
            os.remove(file_path)

        return super().destroy(request, pk)